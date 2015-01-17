import gevent
import random

# Callbacks to be set by external code
send = None
broadcast = None

market = {
	'buy':
	[
		{
			'item': 'water',
			'cost': 1500,
			'display': 'Buy 5 H2O',
		},
		{
			'item': 'grain',
			'cost': 1250,
			'display': 'Buy 5 grain',
		},
		{
			'item': 'water_pack',
			'cost': 5000,
			'display': 'Buy 1 H2O backpack',
		},
		{
			'item': 'build_material',
			'cost': 20000,
			'display': 'Buy 1 build material',
		},
	],
	'sell':
	[
		{
			'item': 'grain',
			'gain': 1000,
			'display': 'Sell 5 grain',
		},
		{
			'item': 'water_pack',
			'gain': 5000,
			'display': 'Sell 1 H2O backpack',
		},
		{
			'item': 'build_material',
			'gain': 15000,
			'display': 'Sell 1 build material',
		},
	],
}

actions = {
	'village':
	[
		{
			'action': 'send_man',
			'display': 'Send man',
			'select': 'man',
		},
		{
			'action': 'send_woman',
			'display': 'Send woman',
		},
		{
			'action': 'send_child',
			'display': 'Send child',
		},
		{
			'action': 'send_grain',
			'display': 'Send 5 grain',
		},
		{
			'action': 'send_water',
			'display': 'Send 5 water',
		},
		{
			'action': 'send_waste',
			'display': 'Send 5 waste',
		},
		{
			'action': 'send_build_material',
			'display': 'Send 1 build material',
		},
		{
			'action': 'send_water_pack',
			'display': 'Send 1 H2O backpack',
		},
	],
	'man':
	[
		{
			'action': 'plow_field',
			'display': 'Plow (+1 field)',
		},
		{
			'action': 'build_hut',
			'display': 'Build hut (-1 build materials, +1 hut)',
		},
		{
			'action': 'work_field',
			'display': 'Work field (+5 grain)',
		},
		{
			'action': 'search_water',
			'display': 'Search for clean water',
		},
		{
            'action': 'dig_well',
			'display': 'Work on well',
			'select': 'well',
		},
	],
	'woman':
	[
		{
			'action': 'work_field',
			'display': 'Work field (+5 grain)',
		},
		{
			'action': 'draw_water',
			'display': 'Draw water (+2 H2O)',
			'select': 'well',
		},
		{
            'action': 'medical_care',
			'display': 'Medical care (-2 grain, -2 water)',
		},
	],
	'child':
	[
		{
			'action': 'draw_water',
			'display': 'Draw water (+1 H2O)',
		},
	],
}

actions_lookup = {
	'village': { x['action']: x for x in actions['village'] },
	'man': { x['action']: x for x in actions['man'] },
	'woman': { x['action']: x for x in actions['woman'] },
	'child': { x['action']: x for x in actions['child'] },
}

market_lookup = {
	'buy': { x['item']: x for x in market['buy'] },
	'sell': { x['item']: x for x in market['sell'] },
}

# Event handlers

def init(world, id):
	if world.village.get(id) is None:
		gevent.spawn(village, world, world.create_village(id))
		for village_id in world.village:
			world.subscribe(id, village_id)
			if village_id != id:
				world.subscribe(village_id, id)

		gevent.spawn(well, world, world.create_well(id))
		for i in xrange(random.randint(3, 8)):
			gevent.spawn(man, world, world.create_man(id))
		for i in xrange(random.randint(3, 8)):
			gevent.spawn(woman, world, world.create_woman(id))
		for i in xrange(random.randint(10, 20)):
			gevent.spawn(child, world, world.create_child(id))

	send(id,
	{
		'init': True,
		'village': id,
		'time_scale': world.time_scale,
		'time': world.time,
		'market': market,
		'actions': actions,
	})

	this_village = world.village[id]
	send(id, {'event': 'Welcome to {0}. Supplies are limited.'.format(this_village['name']) })

	for object_id in world.get_user_subscribed_object_ids(id):
		send(id, world.all[object_id])
	
def buy(world, village, item, amount, msg):
	cost = market_lookup['buy'][item]['cost']
	if village['kwacha'] >= cost:
		village[item] += amount
		village['kwacha'] -= cost
		send(village['id'], { 'event': msg })
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'The merchant takes one look at your coin pouch and laughs you off.' })

def sell(world, village, item, amount, msg):
	gain = market_lookup['sell'][item]['gain']
	if village[item] >= amount:
		village[item] -= amount
		village['kwacha'] += gain
		send(village['id'], { 'event': msg })
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'You don\'t have enough to sell!' })

def action(world, user_id, data):
	village = world.village[user_id]
	village['last_action'] = world.time
	if 'action' not in data:
		print data
	elif data['action'] == 'buy':
		if data['item'] == 'build_material':
			buy(world, village,
				item = 'build_material',
				amount = 1,
				msg = 'You purchase enough material to construct one new hut.'
			)
		elif data['item'] == 'grain':
			buy(world, village,
				item = 'grain',
				amount = 5,
				msg = 'You purchase a small bag of grain.'
			)
		elif data['item'] == 'water':
			buy(world, village,
				item = 'water',
				amount = 5,
				msg = 'You purchase a small container of pure, clean water.'
			)
		elif data['item'] == 'water_packs':
			buy(world, village,
				item = 'water_pack',
				amount = 1,
				msg = 'You purchase a PackH2O water backpack.'
			)
	elif data['action'] == 'sell':
		if data['item'] == 'grain':
			sell(world, village,
				item = 'grain',
				amount = 5,
				msg = 'You sell your grain at a slim but reasonable profit.'
			)
		elif data['item'] == 'water_packs':
			sell(world, village,
				item = 'water_packs',
				amount = 1,
				msg = 'You sell a PackH2O water backpack.'
			)
		elif data['item'] == 'build_material':
			sell(world, village,
				item = 'build_material',
				amount = 1,
				msg = 'You sell enough materials to build one new hut.'
			)
	elif data['action'] == 'task':
		for target_id in data['people']:
			pass

# Processes

def village(world, state):
	while True:
		sent_inaction_message = False
		for _ in xrange(5):
			gevent.sleep(world_seconds(world, 60 * 60 * 4))
			if not sent_inaction_message and world.time - state['last_action'] > 60 * 60 * 4:
				send(state['id'], { 'event': 'Villagers begin to grumble at the inaction of their leader.' })
				sent_inaction_message = True

		gevent.sleep(world_seconds(world, 60 * 60 * 2))

		if world.time - state['last_action'] > 60 * 60 * 48:
			break # The user disconnected

		send(state['id'], { 'event': 'Dawn breaks on a new day in {0}.'.format(state['name']) })

		gevent.sleep(world_seconds(world, 60 * 60 * 2))

		state['waste'] = max(0, state['waste'] - state['huts'] * 2)

		if state['huts'] > 0 and random.randint(0, 5) == 0:
			send(state['id'], { 'event': 'A hut finally collapses under its own weight. Hygeine worsens.' })
			state['huts'] -= 1
			notify(world, state['id'])

		if state['fields'] > 0 and random.randint(0, 5) == 0:
			if len(world.man) > 0:
				worker_id = random.choice(world.man.keys())
				worker = world.man[worker_id]
				send(state['id'], { 'event': '{0} reports one of the fields has been exhausted.'.format(worker['name']) })
			else:
				send(state['id'], { 'event': 'One of your fields has been exhausted.' })
			state['fields'] -= 1
			notify(world, state['id'])

	# Disperse the village
	send_to_subscribers(world, state['id'], { 'event': 'The leader of {0} village cracks under the strain of responsibility. The villagers disperse!'.format(state['name']) })
	# TODO: actually move the villagers

def human(world, state, action_func, normal_awake_time, food_consumption, water_consumption, waste_production, health_threshold):
	awake_time = random.randint(0, normal_awake_time)
	while True:
		loop_start = world.time
		health_start = state['health']

		if is_incapacitated(state):
			gevent.sleep(world_seconds(world, normal_awake_time - awake_time))
		else:
			# TODO: await instruction
			gevent.sleep(world_seconds(world, normal_awake_time - awake_time))

		awake_time += world.time - loop_start

		if awake_time >= normal_awake_time:
			awake_time = 0
			state['state'] = 'sleeping'
			notify(world, state['id'])
			gevent.sleep(world_seconds(world, (60 * 60 * 24) - normal_awake_time + max(0, awake_time - normal_awake_time)))
			state['state'] = None
			village = world.village[state['owner']]
			if village['grain'] > food_consumption:
				village['grain'] -= food_consumption
			else:
				state['health'] -= 1
			if village['water'] > water_consumption:
				village['water'] -= water_consumption
			else:
				state['health'] -= 1
			village['waste'] += waste_production
			notify(world, village['id'])
			if state['health'] <= 0:
				send(state['owner'], { 'event': 'The {1} {0} passes away. The remaining villagers huddle together at a small ceremony.'.format(state['name'], state['type']) })
				notify_delete(world, state['id'])
				world.delete(state['id'])
				break
			elif state['health'] < health_threshold and health_start >= health_threshold:
				state['sick'] = True
				send(state['owner'], { 'event': '{0} ({1}) falls ill and can no longer work.'.format(state['name'], state['type']) })
			elif state['health'] >= health_threshold and health_start < health_threshold:
				state['sick'] = False
				send(state['owner'], { 'event': '{0} ({1}) has recovered sufficiently to continue work'.format(state['name'], state['type']) })
			elif state['health'] >= health_threshold:
				send(state['owner'], { 'event': '{0} ({1}) wakes and requests instruction.'.format(state['name'], state['type']) })
			notify(world, state['id'])

def man(world, state):
	def perform_action(task):
		pass
	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 17,
		food_consumption = 3,
		water_consumption = 3,
		waste_production = 3,
		health_threshold = 5
	)

def woman(world, state):
	def perform_action(task):
		pass
	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 17,
		food_consumption = 2,
		water_consumption = 2,
		waste_production = 2,
		health_threshold = 6
	)

def child(world, state):
	def perform_action(task):
		pass
	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 15,
		food_consumption = 1,
		water_consumption = 1,
		waste_production = 1,
		health_threshold = 4
	)

def well(world, state):
	pass

def timer(world):
	while True:
		gevent.sleep(world_seconds(world, 1))
		world.time += 1
		if world.time % (world.time_scale * 20) == 0:
			broadcast({ 'time': world.time })

# Utilities

def is_incapacitated(person):
	return person['sick'] or person.get('in_labor')

def world_seconds(world, seconds):
	return float(seconds) / world.time_scale

def notify(world, id):
	send_to_subscribers(world, id, world.all[id])

def send_to_subscribers(world, id, data):
	for user_id in world.get_subscribed_user_ids(id):
		send(user_id, data)

def notify_delete(world, id):
	data = world.all[id]
	data['delete'] = True
	for user_id in world.get_subscribed_user_ids(id):
		send(user_id, data)
