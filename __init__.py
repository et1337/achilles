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
import werkzeug.contrib.securecookie

import proc
import state

app = flask.Flask('achilles')

app.config.update(
	DEBUG = True,
	SECRET_KEY = 'dev',
	LOG_FILE = None,
	LOG_FORMAT = '%(asctime)s %(name)s\t%(levelname)s\t%(message)s',
	LOG_LEVEL = logging.INFO,
	ENABLE_BOOTSTRAP = True,
)

world = state.State()

@app.before_request
def make_session_permanent():
	flask.session.permanent = True
	user_id = flask.session.get('id')
	if user_id is None:
		flask.session['id'] = world.create_village()['id']

def wsgi_handler(environ, start_response):
	path = environ.get('PATH_INFO')
	if path == '/feed':
		ws = environ.get('wsgi.websocket')
		if ws:
			return handle_websocket(environ, ws)
	return app(environ, start_response)

websockets = {}

def handle_websocket(environ, ws):
	# Manually load the session
	class FakeRequest(object):
		pass
	fakeRequest = FakeRequest()
	fakeRequest.cookies = werkzeug.utils.parse_cookie(environ)
	session = app.session_interface.open_session(app, fakeRequest)

	user_id = session['id']
	user_sockets = websockets.get(user_id)
	if user_sockets is None:
		user_sockets = websockets[user_id] = []
	user_sockets.append(ws)
	proc.init(world, user_id)
	while True:
		buf = ws.receive()
		if buf is None:
			break
		elif buf:
			proc.action(world, user_id, ujson.decode(buf))
	user_sockets.remove(ws)
	if len(user_sockets) == 0:
		del websockets[user_id]

def send_user(id, msg):
	user_sockets = websockets.get(id)
	if user_sockets is not None:
		for sock in user_sockets:
			sock.send(ujson.encode(msg))

proc.send = send_user

@app.route('/')
def index():
	return flask.render_template('index.html')

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
	port = 4000

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

	final_handler = wsgi_handler
	server = gevent.pywsgi.WSGIServer((host, port), final_handler, handler_class = geventwebsocket.handler.WebSocketHandler, log = log)
	server.serve_forever()
