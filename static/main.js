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
			water_pack: {},
			well: {},
			man: {},
			woman: {},
			child: {},
		},
		ui:
		{
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
		var width = $(window).width();
		$('.panel').width(width);
		$('.panel.level1').css('left', width);
		$('.panel.level2').css('left', width * 2);
		$('.status:not(#status-village)').css('height', $('#status-village').innerHeight());
		$('.items-scroll').height(windowHeight - eventsHeight - $('#status-village').outerHeight());
		$('#horizontal').css('left', state.ui.level * -width);
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
		else if (data.id)
			functions.update(data);
		else if (data.delete)
			functions.delete(data);
	};

	functions.init = function(data)
	{
		state.world.village_id = data.village;
		state.world.time_scale = data.time_scale;
		state.ui.time = data.time;
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
		var data = {
			village: village,
			time: state.ui.time,
			villages: Object.keys(state.world.village).length - 1,
			water_packs: Object.keys(state.world.water_pack).length,
			wells: Object.keys(state.world.well).length,
			men: Object.keys(state.world.man).length,
			women: Object.keys(state.world.woman).length,
			children: Object.keys(state.world.child).length,
		};
		$('.village-name').text(village['name']);
		$('#status-village').html(Mustache.render($('#template-village').html(), data));
		$('#villages').html(Mustache.render($('#template-villages').html(), data));
		$('#men').html(Mustache.render($('#template-men').html(), data));
		$('#women').html(Mustache.render($('#template-women').html(), data));
		$('#children').html(Mustache.render($('#template-children').html(), data));
	};

	functions.next = function(selector)
	{
		state.ui.level++;
		$(selector).show();
		$('#horizontal').animate({ left: $(window).width() * -state.ui.level }, 400);
	};

	functions.back = function()
	{
		state.ui.level--;
		$('#horizontal').animate({ left: $(window).width() * -state.ui.level }, 400, function()
		{
			if (state.ui.level == 1)
				$('.level2').hide();
			if (state.ui.level == 0)
				$('.level1').hide();
		});
	};

	functions.update = function(data)
	{
		var dom_element = null;
		if (state.world.all[data.id])
			dom_element = $('#' + data.id);
		else
		{
			var parent
			dom_element = $('<a id="' + data.id + '">');
		}
		state.world.all[data.id] = data;
		state.world[data.type][data.id] = data;
		functions.update_village_status(data);
	};

	functions.delete = function(data)
	{
		delete state.world.all[data.id];
		delete state.world[data.type][data.id];
		functions.update_village_status(data);
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
		$('.back').click(functions.back);
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
