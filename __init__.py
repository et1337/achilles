#!/usr/bin/env python
import gevent
import gevent.monkey
import gevent.socket
gevent.monkey.patch_all()

import os

import gevent.queue
import gevent.event
import ujson

import flask

import logging

app = flask.Flask('achilles')

app.config.update(
	DEBUG = True,
	SECRET_KEY = 'dev',
	LOG_FILE = None,
	LOG_FORMAT = '%(asctime)s %(name)s\t%(levelname)s\t%(message)s',
	LOG_LEVEL = logging.INFO,
	ENABLE_BOOTSTRAP = True,
)

@app.before_request
def make_session_permanent():
    flask.session.permanent = True

def handler(environ, start_response):
	handled = False
	path = environ['PATH_INFO']
	if path == '/feed':
		ws = environ.get('wsgi.websocket')
		if ws:
			handle_websocket(ws, path[6:])
			handled = True
	
	if not handled:
		return app(environ, start_response)

websockets = {}

def handle_websocket(ws, env):
	if not env:
		env = BOOTSTRAP_ENV

	s = websockets.get(env)
	if s is None:
		s = websockets[env] = []
	s.append(ws)

	s.send(ujson.encode({'test': 'yo'}))

	while True:
		buf = ws.receive()
		if buf is None:
			break

	if ws in s:
		s.remove(ws)

@app.route('/feed')
def feed(env = None):
	flask.abort(400)

greenlets = {}

def broadcast(env, packet):
	sockets = websockets.get(env)
	if sockets is not None:
		packet = ujson.encode(packet)
		for ws in list(sockets):
			if ws.socket is not None:
				try:
					ws.send(packet)
				except gevent.socket.error:
					if ws in sockets:
						sockets.remove(ws)

@app.route('/test', methods = ['POST'])
def test():
	return ujson.encode(
	{
		'status': 'ok'
	})

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.template_filter('urlquote')
def urlquote(url):
	return urllib.quote(url, '')

@app.route('/favicon.ico')
def favicon():
	return flask.send_from_directory(
		os.path.join(app.root_path, 'static'),
		'favicon.ico',
		mimetype = 'image/vnd.microsoft.icon',
	)

if __name__ == '__main__':
	import geventwebsocket.handler
	import gevent.pywsgi
	import logging
	import sys

	if len(sys.argv) > 1:
		app.config.from_pyfile(sys.argv[1])

	host = '0.0.0.0'
	port = 5000

	server_name = app.config.get('SERVER_NAME')
	if server_name is not None and ':' in server_name:
		server_name = server_name.split(':')
		host = server_name[0]
		port = int(server_name[1])
	
	log = 'default'

	if not app.debug:
		log = None
		filename = app.config['LOG_FILE']
		if filename:
			handler = logging.FileHandler(filename)
			handler.setLevel(app.config['LOG_LEVEL'])

			formatter = logging.Formatter(chefdash.app.config['LOG_FORMAT'])
			handler.setFormatter(formatter)

			app.logger.setLevel(chefdash.app.config['LOG_LEVEL'])
			app.logger.addHandler(handler)
	
	app.logger.info('Listening on %s:%d' % (host, port))

	final_handler = handler
	if app.debug:
		from werkzeug.debug import DebuggedApplication
		final_handler = DebuggedApplication(handler, True)
	server = gevent.pywsgi.WSGIServer((host, port), final_handler, handler_class = geventwebsocket.handler.WebSocketHandler, log = log)
	server.serve_forever()
