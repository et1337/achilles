import state

send = None # Callback to be set by external code

def action(world, id, msg):
	print msg

def init(world, id):
	if world.village.get(id) is None:
		world.create_village(id)
	send(id, { 'init': id })
	send(id, world.village[id])
