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
			selected: {},
			width: 0,
			time: 0,
			level: 0,
		},
	};

	var functions = {};

	functions.resize = function()
	{
		var windowHeight = $(window).innerHeight();
		$('#events-scroll').height(windowHeight * 0.2);
		var eventsHeight = $('#events-scroll').outerHeight();
		$('#horizontal-scroll').height(windowHeight - eventsHeight);
		state.ui.width = $(window).width();
		$('.panel').width(state.ui.width);
		$('.panel.level1').css('left', state.ui.width);
		$('.panel.level2').css('left', state.ui.width * 2);
		$('.status:not(#status-village)').css('height', $('#status-village').height());
		$('.items-scroll').height(windowHeight - eventsHeight - $('#status-village').outerHeight());
		$('#horizontal').css('left', state.ui.level * -state.ui.width);
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

	functions.init = function(data)
	{
		$('#events').html('');
		functions.back(0);
		all = $.extend(true, {}, state.world.all);
		for (var id in all)
			functions.delete(all[id])

		$('#buy-grain').html(Mustache.render($('#template-buy-grain').html(), data));
		$('#sell-grain').html(Mustache.render($('#template-sell-grain').html(), data));
		$('#buy-water').html(Mustache.render($('#template-buy-water').html(), data));
		$('#sell-water').html(Mustache.render($('#template-sell-water').html(), data));
		$('#buy-water_pack').html(Mustache.render($('#template-buy-water_pack').html(), data));
		$('#sell-water_pack').html(Mustache.render($('#template-sell-water_pack').html(), data));
		$('#buy-build_material').html(Mustache.render($('#template-buy-build_material').html(), data));
		$('#sell-build_material').html(Mustache.render($('#template-sell-build_material').html(), data));
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
			var data = {
				village: village,
				time: state.ui.time,
				villages: Object.keys(state.world.village).length - 1,
				wells: Object.keys(state.world.well).length,
				men: Object.keys(state.world.man).length,
				women: Object.keys(state.world.woman).length,
				children: Object.keys(state.world.child).length,
			};
			$('.village-name').text(village.name);
			$('#status-village-contents').html(Mustache.render($('#template-main-village').html(), data));
			$('#villages').html(Mustache.render($('#template-villages').html(), data));
			$('#men').html(Mustache.render($('#template-men').html(), data));
			$('#women').html(Mustache.render($('#template-women').html(), data));
			$('#children').html(Mustache.render($('#template-children').html(), data));
			$('.status:not(#status-village)').css('height', $('#status-village').height());
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
			var $dom_element = null;
			if (state.world.all[data.id])
				$dom_element = $('#' + data.id);
			else
			{
				var $parent = $('#items-' + data.type);
				$dom_element = $('<a class-"' + data.type + '" id="' + data.id + '">');
				$parent.append($dom_element);
				functions.bind_object_handlers(data.id, $dom_element);
			}
			$dom_element.html(Mustache.render($('#template-' + data.type).html(), data));
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
		$('#villages').click(function() { functions.next('#village') });
		$('#men').click(function() { functions.next('#man') });
		$('#women').click(function() { functions.next('#woman') });
		$('#children').click(function() { functions.next('#child') });
		$('.back').click(function() { functions.back(); });
		$('#market').click(function() { functions.next('#actions-market') });
		$('#buy-grain').click(function() { functions.send({ 'action': 'buy', 'resource': 'grain' }) });
		$('#sell-grain').click(function() { functions.send({ 'action': 'sell', 'resource': 'grain' }) });
		$('#buy-water').click(function() { functions.send({ 'action': 'buy', 'resource': 'water' }) });
		$('#sell-water').click(function() { functions.send({ 'action': 'sell', 'resource': 'water' }) });
		$('#buy-water_pack').click(function() { functions.send({ 'action': 'buy', 'resource': 'water_packs' }) });
		$('#sell-water_pack').click(function() { functions.send({ 'action': 'sell', 'resource': 'water_packs' }) });
		$('#buy-build_material').click(function() { functions.send({ 'action': 'buy', 'resource': 'build_material' }) });
		$('#sell-build_material').click(function() { functions.send({ 'action': 'sell', 'resource': 'build_material' }) });
		$('#actions-man-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-man') });
		$('#actions-woman-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-woman') });
		$('#actions-child-next').click(function() { if (!$(this).hasClass('disabled')) functions.next('#actions-child') });
	};

	functions.bind_object_handlers = function(id, $object)
	{
		$object.click(function() { functions.click_object(id, $object) });
	};

	functions.click_object = function(id, $object)
	{
		var object = state.world.all[id];
		$object.toggleClass('selected');
		if (state.ui.selected[id])
			delete state.ui.selected[id];
		else
			state.ui.selected[id] = true;
		functions.update_next_button_state();
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
