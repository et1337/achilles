(function()
{
	var state =
	{
		ws: null,
		world:
		{
			time_scale: 1,
			village_id: null,
			all: {},
			village: {},
			well: {},
			man: {},
			woman: {},
			child: {},
		},
		ui:
		{
			current_action: null,
			selected: {},
			width: 0,
			time: 0,
			level: 0,
		},
	};

	var functions = {};

	functions.resize = function()
	{
		var windowHeight = $(window).height();
		$('#events-scroll').height(windowHeight * 0.2);
		var eventsHeight = $('#events-scroll').outerHeight();
		$('#horizontal-scroll').height(windowHeight - eventsHeight);
		state.ui.width = $(window).width();
		$('.panel').width(state.ui.width);
		functions.update_panel_position(0, $('.level0'));
		functions.update_panel_position(1, $('.level1'));
		functions.update_panel_position(2, $('.level2'));
		functions.update_panel_position(3, $('.level3'));
		$('.status:not(#status-village)').css('height', $('#status-village').height());
		$('.items-scroll').height(windowHeight - eventsHeight - $('#status-village').outerHeight());
		$('#horizontal').css('left', state.ui.level * -state.ui.width);
	};

	functions.update_panel_position = function(level, $panel)
	{
		$panel.css('left', state.ui.width * level);
	};

	functions.timer = function()
	{
		state.ui.time += 60;
		var date = new Date((86400 * 50 + state.ui.time) * 1000);
		$('#time').text(date.getMonth() + '/' + date.getDate() + ' ' + date.getHours() + ':00');
		setTimeout(functions.timer, 60000 / state.world.time_scale);
	};

	functions.onmessage = function(msg)
	{
		var data = JSON.parse(msg.data);
		if (data.init)
			functions.init(data);
		else if (data.event)
			functions.event(data);
		else if (data.delete)
			functions.delete(data);
		else if (data.id)
			functions.update(data);
		functions.update_village_status();
	};

	functions.template_preprocess = function(data)
	{
		var x1 = data['x'], y1 = data['y'];
		if (x1 !== undefined && y1 !== undefined)
		{
			var village = state.world.village[state.world.village_id];
			var x_dist = village.x - x1, y_dist = village.y - y1;
			var newData = $.extend({}, data);
			newData.distance = Math.floor(Math.sqrt((x_dist * x_dist) + (y_dist * y_dist))) * 0.001;
			return newData;
		}
		return data;
	};

	functions.template = function(template_selector, data)
	{
		var preprocessed_data = functions.template_preprocess(data);
		var template = $(template_selector).html();
		return Mustache.render(template, preprocessed_data);
	};

	functions.init = function(data)
	{
		$('#events').html('');
		functions.back(0);
		all = $.extend(true, {}, state.world.all);
		for (var id in all)
			functions.delete(all[id])

		$('#market .items').html(functions.template('#template-items-market', data.market));
		$('#actions-village .items').html(functions.template('#template-action-items', data.actions.village));
		$('#actions-man .items').html(functions.template('#template-action-items', data.actions.man));
		$('#actions-woman .items').html(functions.template('#template-action-items', data.actions.woman));
		$('#actions-child .items').html(functions.template('#template-action-items', data.actions.child));
		$('.actions a').click(function() { functions.action($(this).attr('action'), $(this).attr('select')) });
		$('#market .items .buy').click(function() { functions.buy($(this).attr('item')) });
		$('#market .items .sell').click(function() { functions.sell($(this).attr('item')) });
		state.world.village_id = data.village;
		state.world.time_scale = data.time_scale;
		var duration = (3600.0 / data.time_scale).toString() + 's';
		$('.pie').attr('style', 'animation-duration: ' + duration + '; -webkit-animation-duration: ' + duration + '; -moz-animation-duration: ' + duration);
		$('.pie').hide().show(0); // Force repaint
		var should_start_timer = state.ui.time == 0;
		state.ui.time = data.time;
		if (should_start_timer)
			functions.timer();
	};

	functions.action = function(action, select)
	{
		if (select)
		{
			state.ui.current_action = action;
			functions.next('#' + select);
			var $panel = $('#' + select);
			$panel.removeClass('level0');
			$panel.removeClass('level1');
			$panel.removeClass('level2');
			$panel.addClass('level3');
			functions.update_panel_position(3, $panel);
		}
		else
		{
			functions.send(
			{
				'action': action,
				'targets': Object.keys(state.ui.selected),
			});
			functions.back(1);
		}
	};

	functions.buy = function(item)
	{
		functions.send(
		{
			'action': 'buy',
			'item': item,
		});
	};

	functions.sell = function(item)
	{
		functions.send(
		{
			'action': 'sell',
			'item': item,
		});
	};

	functions.event = function(data)
	{
		var p = $('<p>');
		p.text(data.event);
		p.hide();
		$('#events').append(p);
		p.fadeIn();
		$("#events-scroll").scrollTop($("#events-scroll")[0].scrollHeight);
	};

	functions.update_village_status = function()
	{
		var village = state.world.village[state.world.village_id];
		if (village)
		{
			var men = 0, idle_men = 0;
			for (var man_id in state.world.man)
			{
				men++;
				if (state.world.man[man_id]['state'] == null)
					idle_men++;
			}

			var women = 0, idle_women = 0;
			for (var woman_id in state.world.woman)
			{
				women++;
				if (state.world.woman[woman_id]['state'] == null)
					idle_women++;
			}

			var children = 0, idle_children = 0;
			for (var child_id in state.world.child)
			{
				children++;
				if (state.world.child[child_id]['state'] == null)
					idle_children++;
			}

			var data = {
				'village': village,
				'time': state.ui.time,
				'villages': Object.keys(state.world.village).length - 1,
				'wells': Object.keys(state.world.well).length,
				'men': men,
				'idle_men': idle_men,
				'women': women,
				'idle_women': idle_women,
				'children': children,
				'idle_children': idle_children,
			};
			$('.village-name').text(village.name);
			$('#status-village-contents').html(functions.template('#template-main-village', data));
			$('#button-villages').html(functions.template('#template-villages', data));
			$('#button-men').html(functions.template('#template-men', data));
			$('#button-women').html(functions.template('#template-women', data));
			$('#button-children').html(functions.template('#template-children', data));
			$('.status:not(#status-village)').css('height', $('#status-village').height());
		}
		functions.update_next_button_state();
	};

	functions.toggle_select_all = function($selector)
	{
		var $total = $selector.filter(':not(.disabled)');
		var $selected = $selector.filter('.selected');
		if ($selected.length > $total.length - $selected.length) // Deselect all
		{
			state.ui.selected = {};
			$selected.removeClass('selected');
		}
		else
		{
			$total.addClass('selected');
			$total.each(function()
			{
				state.ui.selected[$(this).attr('id')] = true;
			});
		}
		functions.update_next_button_state();
	};

	functions.next = function(selector)
	{
		state.ui.level++;
		$(selector).show();
		$('#horizontal').animate({ left: state.ui.width * -state.ui.level }, 250);
	};

	functions.back = function(to_level)
	{
		state.ui.current_action = null;
		if (to_level === undefined)
			state.ui.level--;
		else
			state.ui.level = to_level;
		if (state.ui.level == 0)
		{
			state.ui.selected = {};
			$('.items a.selected').removeClass('selected');
		}
		$('#horizontal').animate({ left: state.ui.width * -state.ui.level }, 250, function()
		{
			if (state.ui.level <= 2)
				functions.update_panel_position(1, $('.level3').removeClass('.level3').addClass('.level1').hide());
			if (state.ui.level <= 1)
				$('.level2').hide();
			if (state.ui.level == 0)
				$('.level1').hide();
		});
	};

	functions.update = function(data)
	{
		if (data.id != state.world.village_id)
		{
			var $newElement = $(functions.template('#template-' + data.type, data));
			if (state.world.all[data.id])
				$('#' + data.id).replaceWith($newElement);
			else
				$('#' + data.type + ' .items').append($newElement);
			functions.bind_object_handlers($newElement);
			if (state.ui.selected[data.id])
			{
				if ($newElement.hasClass('disabled'))
					delete state.ui.selected[data.id];
				else
					$newElement.addClass('selected');
			}
		}
		state.world.all[data.id] = data;
		state.world[data.type][data.id] = data;
	};

	functions.delete = function(data)
	{
		if (state.ui.selected[data.id])
			delete state.ui.selected[data.id];
		$('#' + data.id).remove();
		delete state.world.all[data.id];
		delete state.world[data.type][data.id];
	};

	functions.onclose = function()
	{
		setTimeout(function()
		{
			if (state.ws != null && state.ws.readyState != 1)
				functions.connect();
		}, 2000);
	};

	functions.connect = function()
	{
		state.ws = new WebSocket((window.location.protocol == 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/feed');
		state.ws.onmessage = functions.onmessage;
		state.ws.onclose = functions.onclose;
	};

	functions.bind_handlers = function()
	{
		$('#button-villages').click(function() { functions.next('#village') });
		$('#button-men').click(function() { functions.next('#man') });
		$('#button-women').click(function() { functions.next('#woman') });
		$('#button-children').click(function() { functions.next('#child') });
		$('#button-market').click(function() { functions.next('#market') });
		$('.back').click(function() { functions.back(); });
		$('#actions-village-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-village') });
		$('#actions-man-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-man') });
		$('#actions-woman-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-woman') });
		$('#actions-child-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-child') });
		$('.select-all').click(function() { functions.toggle_select_all($(this).siblings()) });
	};

	functions.bind_object_handlers = function($object)
	{
		$object.click(function() { functions.select($object) });
	};

	functions.select = function($object)
	{
		if (!$object.hasClass('disabled'))
		{
			var id = $object.attr('id');
			if (state.ui.level == 3 && state.ui.current_action)
			{
				functions.send(
				{
					'action': state.ui.current_action,
					'targets': Object.keys(state.ui.selected),
					'select': id,
				});
				functions.back(1);
			}
			else
			{
				var object = state.world.all[id];
				$object.toggleClass('selected');
				if (state.ui.selected[id])
					delete state.ui.selected[id];
				else
					state.ui.selected[id] = true;
				functions.update_next_button_state();
			}
		}
	};

	functions.update_next_button_state = function()
	{
		if (Object.keys(state.ui.selected).length == 0)
			$('.next').addClass('disabled');
		else
			$('.next').removeClass('disabled');
	};

	functions.send = function(data)
	{
		if (state.ws != null && state.ws.readyState == 1)
			state.ws.send(JSON.stringify(data));
	};
	
	$(document).ready(functions.resize);
	$(document).ready(functions.bind_handlers);
	$(window).resize(functions.resize);
	$(document).ready(functions.connect);

	setInterval(function()
	{
		if (state.ws != null && state.ws.readyState == 1)
			state.ws.send(''); // Keep websocket alive
	}, 20000);
})();
