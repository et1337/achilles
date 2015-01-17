import state
import gevent

# Callbacks to be set by external code
send = None
broadcast = None

def action(world, id, msg):
	print msg

def init(world, id):
	if world.village.get(id) is None:
		world.create_village(id)
	send(id,
	{
		'init': True,
		'village': id,
		'time_scale': world.time_scale,
		'time': world.time,
	})
	village = world.village[id]
	send(id, village)
	send(id, {'event': 'Welcome to {0}. Supplies are limited.'.format(village['name']) })

def timer(world):
	while True:
		gevent.sleep(1.0 / world.time_scale)
		world.time += 1
		if world.time % (world.time_scale * 20) == 0:
			broadcast({ 'time': world.time })
