var ws = null;

function resize()
{
	var windowHeight = $(window).innerHeight();
	$('#events-scroll').height(windowHeight * 0.2);
	var eventsHeight = $('#events-scroll').outerHeight();
	$('#horizontal-scroll').height(windowHeight - eventsHeight);
	$('.panel').width($(window).width());
	$('#items-scroll').height(windowHeight - eventsHeight - $('.status').outerHeight());
}
$(document).ready(resize);
$(window).resize(resize);

function onmessage(msg)
{
	var data = JSON.parse(msg.data);
	if (data.init)
		$('#status-village').attr('id', 'status-' + data.init);
	else if (data.event)
	{
		var p = $('<p>');
		p.text(data.event);
		$('#events').append(p);
	}
	else if (data.id)
		$('#status-' + data.id).text(JSON.stringify(data));
}

function onclose()
{
	setTimeout(function()
	{
		if (ws != null && ws.readyState != 1)
			connect();
	}, 2000);
}

function connect()
{
	ws = new WebSocket((window.location.protocol == 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/feed');
	ws.onmessage = onmessage;
	ws.onclose = onclose;
}

$(document).ready(connect);

setInterval(function()
{
	if (ws != null && ws.readyState == 1)
		ws.send(''); // Keep websocket alive
}, 20000);
