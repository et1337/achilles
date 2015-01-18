import gevent
import gevent.event
import random
import math
import copy

# Callbacks to be set by external code
send = None
broadcast = None

commands = {}
well_notifications = {}

WELL_DRAW_TIME = 30 * 60

WALK_SPEED = 0.4

MARKET = {
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
			'item': 'water_packs',
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
			'item': 'water_packs',
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

ACTIONS = {
	'village':
	[
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
			'display': 'Dig well',
			'select': 'well',
		},
		{
			'action': 'send',
			'display': 'Send to neighbor village',
			'select': 'village',
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
            'action': 'heal_man',
			'display': 'Heal man (-2 grain)',
			'select': 'man',
		},
		{
            'action': 'heal_woman',
			'display': 'Heal woman (-2 grain)',
			'select': 'woman',
		},
		{
            'action': 'heal_child',
			'display': 'Heal child (-1 grain)',
			'select': 'child',
		},
		{
			'action': 'send',
			'display': 'Send to neighbor village',
			'select': 'village',
		},
	],
	'child':
	[
		{
			'action': 'draw_water',
			'display': 'Draw water (+1 H2O)',
			'select': 'well',
		},
		{
			'action': 'send',
			'display': 'Send to neighbor village',
			'select': 'village',
		},
	],
}

MARKET_LOOKUP = {
	'buy': { x['item']: x for x in MARKET['buy'] },
	'sell': { x['item']: x for x in MARKET['sell'] },
}

# Event handlers

def init(world, id):
	if world.village.get(id) is None:
		village_instance = world.create_village(id)
		gevent.spawn(village, world, village_instance)
		notify(world, id)
		for village_id in world.village:
			if village_id != id:
				send(village_id, { 'events': 'The nearby village of {0} establishes friendly contact.'.format(village_instance['name']) })

		instance = world.create_well(id, 100)
		gevent.spawn(well, world, instance)
		notify(world, instance['id'])
		for i in xrange(random.randint(3, 8)):
			instance = world.create_man(id)
			gevent.spawn(man, world, instance)
			notify(world, instance['id'])
		for i in xrange(random.randint(3, 8)):
			instance = world.create_woman(id)
			gevent.spawn(woman, world, instance)
			notify(world, instance['id'])
		for i in xrange(random.randint(5, 12)):
			instance = world.create_child(id)
			gevent.spawn(child, world, instance)
			notify(world, instance['id'])

	send(id,
	{
		'init': True,
		'village': id,
		'time_scale': world.time_scale,
		'time': world.time,
		'market': MARKET,
		'actions': ACTIONS,
	})

	this_village = world.village[id]
	send(id, {'event': '{0}, Malawi welcomes you.'.format(this_village['name']) })

	for object_id in world.get_user_subscribed_object_ids(id):
		send(id, world.all[object_id])
	
def buy(world, village, item, amount, msg):
	cost = MARKET_LOOKUP['buy'][item]['cost']
	if village['kwacha'] >= cost:
		village[item] += amount
		village['kwacha'] -= cost
		send(village['id'], { 'event': msg })
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'The merchant takes one look at your billfold and laughs you off.' })

def sell(world, village, item, amount, msg):
	gain = MARKET_LOOKUP['sell'][item]['gain']
	if village[item] >= amount:
		village[item] -= amount
		village['kwacha'] += gain
		send(village['id'], { 'event': msg })
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'You don\'t have enough to sell!' })

def send_resource(world, village, target_ids, resource, display, amount):
	if village[resource] >= amount * len(target_ids):
		for target_id in target_ids:
			target = world.village[target_id]
			target[resource] += amount
			village[resource] -= amount
			notify(world, target['id'])
			send(target['id'], { 'event': '{0} {1} arrives from {2}.'.format(amount, display, village['name']) })
			send(village['id'], { 'event': 'You send {0} {1} to {2}.'.format(amount, display, target['name']) })
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'Not enough on hand to send!' })

def action(world, user_id, data):
	village = world.village[user_id]
	village['last_action'] = world.time
	if 'action' in data:
		if data['action'] == 'buy':
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
					item = 'water_packs',
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
		elif data['action'] == 'send_grain':
			send_resource(world, village, data['targets'], 'grain', 'grain', 5)
		elif data['action'] == 'send_water':
			send_resource(world, village, data['targets'], 'water', 'water', 5)
		elif data['action'] == 'send_waste':
			send_resource(world, village, data['targets'], 'waste', 'waste', 5)
		elif data['action'] == 'send_build_material':
			send_resource(world, village, data['targets'], 'build_material', 'build material', 1)
		elif data['action'] == 'send_water_pack':
			send_resource(world, village, data['targets'], 'water_packs', 'H2O backpack', 1)
		elif 'targets' in data:
			targets = data['targets']
			for target_id in targets:
				target = world.all[target_id]
				if target.get('state') == None:
					command = commands.get(target_id)
					if command is not None:
						command.set(data)

# Processes

def village(world, state):
	sent_inactivity_message = False
	while True:
		for _ in xrange(5):
			gevent.sleep(world_seconds(world, 60 * 60 * 4))
			if not sent_inactivity_message and world.time - state['last_action'] > 60 * 60 * 11:
				send(state['id'], { 'event': 'Villagers begin to grumble at the inactivity of their leader.' })
				sent_inactivity_message = True
		sent_inactivity_message = False

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

	# Disperse the village
	send_to_subscribers(world, state['id'], { 'event': 'The leader of {0} village cracks under the strain of responsibility. The villagers disperse!'.format(state['name']) })
	villages = world.village.keys()
	villages.remove(state['id'])
	if len(villages) > 0:
		for man_id in world.man:
			man = world.man[man_id]
			transplant(world, man, random.choice(villages))
		for woman_id in world.woman:
			woman = world.woman[woman_id]
			transplant(world, woman, random.choice(villages))
		for child_id in world.child:
			child = world.child[child_id]
			transplant(world, child, random.choice(villages))

def transplant(world, person, new_village_id):
	old_village = world.village[person['owner']]
	new_village = world.village[new_village_id]
	notify_delete(world, person['id'])
	world.subscribe(new_village['id'], person['id'])
	world.unsubscribe(old_village['id'], person['id'])
	person['owner'] = new_village['id']
	notify(world, person['id'])

def human(world, state, action_func, normal_awake_time, food_consumption, water_consumption, waste_production, health_threshold):
	awake_time = random.randint(0, normal_awake_time)
	command = commands[state['id']] = gevent.event.AsyncResult()
	while True:
		loop_start = world.time
		health_start = state['health']

		if is_incapacitated(state):
			gevent.sleep(world_seconds(world, normal_awake_time - awake_time))
		else:
			task = command.wait(world_seconds(world, normal_awake_time - awake_time))
			if task is not None:
				command = commands[state['id']] = gevent.event.AsyncResult()
				action_func(task)

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
				break
			elif state['health'] < health_threshold and health_start >= health_threshold:
				state['sick'] = True
				send(state['owner'], { 'event': '{0} ({1}) falls ill and can no longer work.'.format(state['name'], state['type']) })
			elif state['health'] >= health_threshold and health_start < health_threshold:
				state['sick'] = False
				send(state['owner'], { 'event': '{0} ({1}) has recovered sufficiently to continue work'.format(state['name'], state['type']) })
			notify(world, state['id'])

	del commands[state['id']]
	send(state['owner'], { 'event': 'The {1} {0} passes away. The remaining villagers huddle together at a small ceremony.'.format(state['name'], state['type']) })
	notify_delete(world, state['id'])
	world.delete(state['id'])

def work_field(world, state, world_time, result_amount):
	village = world.village[state['owner']]
	if village['free_fields'] > 0:
		village['free_fields'] -= 1

		notify(world, village['id'])
		state['state'] = 'working'
		notify(world, state['id'])
		gevent.sleep(world_seconds(world, world_time))
		state['state'] = None
		notify(world, state['id'])
		village['grain'] += result_amount
		if random.randint(0, 10) == 0:
			village['fields'] -= 1
			send(village['id'], { 'event': '{0} reports one of the fields has been exhausted.'.format(state['name']) })
		else:
			village['free_fields'] += 1
		notify(world, village['id'])
	else:
		send(village['id'], { 'event': 'No fields available.' })

def send_human(world, state, village_id):
	old_village = world.village[state['owner']]
	new_village = world.village[village_id]
	send(old_village['id'], { 'event': '{0} embarks for the village of {1}.'.format(state['name'], new_village['name']) })
	notify_delete(world, state['id'])
	world.subscribe(new_village['id'], state['id'])
	world.unsubscribe(old_village['id'], state['id'])
	send(new_village['id'], { 'event': '{0} is set to arrive soon from the village of {1}.'.format(state['name'], old_village['name']) })
	state['owner'] = new_village['id']
	state['state'] = 'traveling'
	notify(world, state['id'])
	gevent.sleep(world_seconds(world, distance(old_village, new_village) / WALK_SPEED))
	state['state'] = None
	notify(world, state['id'])

def man(world, state):
	def perform_action(task):
		village = world.village[state['owner']]
		if task['action'] == 'plow_field':
			state['state'] = 'plowing'
			notify(world, state['id'])
			gevent.sleep(world_seconds(world, 60 * 60 * 17))
			village['fields'] += 1
			village['free_fields'] += 1
			notify(world, village['id'])
			state['state'] = None
			notify(world, state['id'])
			send(state['owner'], { 'event': '{0} finished plowing a field.'.format(state['name']) })
		elif task['action'] == 'build_hut':
			if village['build_material'] > 0:
				village['build_material'] -= 1
				notify(world, village['id'])
				state['state'] = 'building'
				notify(world, state['id'])
				gevent.sleep(world_seconds(world, 60 * 60 * 17))
				village['huts'] += 1
				notify(world, village['id'])
				state['state'] = None
				notify(world, state['id'])
			else:
				send(village['id'], { 'event': 'Not enough material on hand to build a hut.' })
		elif task['action'] == 'search_water':
			state['state'] = 'searching'
			notify(world, state['id'])
			gevent.sleep(world_seconds(world, 60 * 60 * 8))
			state['state'] = None
			notify(world, state['id'])
			if random.randint(0, 6) == 0:
				well_instance = world.create_well(state['owner'])
				gevent.spawn(well, world, well_instance)
				notify(world, well_instance['id'])
				send_to_subscribers(world, state['id'], { 'event': '{0} discovers {1}.'.format(state['name'], well_instance['name']) })
			else:
				send(state['owner'], { 'event': '{0}\'s search for water is unsuccessful.'.format(state['name']) })
		elif task['action'] == 'dig_well':
			state['state'] = 'digging'
			notify(world, state['id'])
			gevent.sleep(world_seconds(world, 60 * 60 * 8))
			state['state'] = None
			notify(world, state['id'])
			target_well = world.well.get(task['select'])
			if target_well is not None:
				old_complete = target_well['complete']
				target_well['complete'] = min(100, target_well['complete'] + 15)
				if old_complete < 100 and target_well['complete'] == 100:
					send_to_subscribers(world, target_well['id'], { 'event': '{0} is complete.'.format(target_well['name']) })
				notify(world, target_well['id'])
		elif task['action'] == 'send':
			send_human(world, state, task['select'])
		elif task['action'] == 'work_field':
			work_field(world, state, world_time = 60 * 60 * 10, result_amount = 5)

	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 17,
		food_consumption = 3,
		water_consumption = 3,
		waste_production = 3,
		health_threshold = 5
	)

def distance(a, b):
	x_diff = a['x'] - b['x']
	y_diff = a['y'] - b['y']
	return math.sqrt((x_diff * x_diff) + (y_diff * y_diff))

def draw_water(world, state, well_id, amount):
	village = world.village[state['owner']]
	well = world.well[well_id]

	if well['complete'] < 100:
		send(state['owner'], { 'event': '{0} is not complete yet!'.format(well['name']) })
		return

	if village['water_packs'] > 0:
		village['water_packs'] -= 1
		notify(world, village['id'])
		amount *= 2
		state['water_pack'] = True
	state['state'] = 'walking'
	notify(world, state['id'])
	walk_world_time = distance(village, well) / WALK_SPEED
	gevent.sleep(world_seconds(world, walk_world_time))
	state['state'] = 'waiting'
	notify(world, state['id'])
	drew = False
	if world.well.get(well_id) is not None: # The well hasn't dried up yet
		well_notification = well_notifications[state['id']] = gevent.event.AsyncResult()
		well['queue'].append(state['id'])
		if well_notification.get():
			state['state'] = 'drawing'
			notify(world, state['id'])
			gevent.sleep(world_seconds(world, WELL_DRAW_TIME))
			drew = True
	state['state'] = 'walking'
	notify(world, state['id'])
	gevent.sleep(world_seconds(world, walk_world_time))
	state['state'] = None
	if state['water_pack']:
		state['water_pack'] = False
		village['water_pack'] -= 1
	notify(world, state['id'])
	if drew:
		village['water'] += amount
	notify(world, village['id'])

def woman(world, state):
	def perform_action(task):
		if task['action'] == 'draw_water':
			draw_water(world, state, task['select'], 2)
		elif task['action'] == 'send':
			send_human(world, state, task['select'])
		elif task['action'] == 'heal_man' or task['action'] == 'heal_woman' or task['action'] == 'heal_child':
			target = world.all.get(task['select'])
			if target is not None:
				cost = 2
				if target['type'] == 'child':
					cost = 1
				if target['state'] == 'sleeping' or target['state'] is None:
					if target['health'] < target['max_health']:
						village = world.village[state['owner']]
						if village['grain'] >= cost:
							village['grain'] -= cost
							notify(world, village['id'])
							target['state'] = 'being healed'
							notify(world, target['id'])
							state['state'] = 'healing'
							notify(world, state['id'])
							gevent.sleep(world_seconds(world, 60 * 60 * 5))
							target['health'] = min(target['max_health'], target['health'] + 1)
							notify(world, target['id'])
							if target['health'] < target['max_health']:
								gevent.sleep(world_seconds(world, 60 * 60 * 5))
								target['health'] = min(target['max_health'], target['health'] + 1)
								notify(world, target['id'])
							target['state'] = None
							notify(world, target['id'])
							state['state'] = None
							notify(world, state['id'])
						else:
							send(state['owner'], { 'event': 'Not enough grain to heal!' })
					else:
						send(state['owner'], { 'event': 'Individual does not need healing.' })
				else:
					send(state['owner'], { 'event': 'Individual must be idle or sleeping to be healed.' })
		elif task['action'] == 'work_field':
			work_field(world, state, world_time = 60 * 60 * 10, result_amount = 5)

	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 17,
		food_consumption = 2,
		water_consumption = 2,
		waste_production = 2,
		health_threshold = 5
	)

def child(world, state):
	def perform_action(task):
		if task['action'] == 'draw_water':
			draw_water(world, state, task['select'], 1)
		elif task['action'] == 'send':
			send_human(world, state, task['select'])

	human(world, state, perform_action,
		normal_awake_time = 60 * 60 * 15,
		food_consumption = 1,
		water_consumption = 1,
		waste_production = 1,
		health_threshold = 4
	)

def well(world, state):
	queue = state['queue']
	lastQueue = len(queue)
	while True:
		if len(queue) != lastQueue:
			lastQueue = len(queue)
			notify(world, state['id'])

		can_run_dry = False
		if len(queue) > 0:
			human_id = queue.pop(0)
			well_notifications[human_id].set(True)
			del well_notifications[human_id]
			can_run_dry = True
		gevent.sleep(world_seconds(world, WELL_DRAW_TIME))
		if can_run_dry and random.randint(0, 60) == 0:
			break

	for human_id in queue:
		well_notifications[human_id].set(False)
		del well_notifications[human_id]
	send_to_subscribers(world, state['id'], { 'event': '{0} runs dry.'.format(state['name']) })
	notify_delete(world, state['id'])
	world.delete(state['id'])

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
	data = copy.deepcopy(world.all[id])
	data['delete'] = True
	for user_id in world.get_subscribed_user_ids(id):
		send(user_id, data)
