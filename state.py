import uuid
import random
import data

def village_name():
	return random.choice(data.villages)

def person_name():
	return '{0} {1}'.format(random.choice(data.names), random.choice(data.names))

class State(object):
	def __init__(self):
		self.time_scale = 1
		self.time = 0
		self.all = {}
		self.village = {}
		self.man = {}
		self.woman = {}
		self.child = {}
		self.well = {}
		self.user_to_object_subscription = {}
		self.object_to_user_subscription = {}
		self.well_index = random.randint(1, 17)
	
	def create_village(self, id = None):
		i = self.create('village', None, id)
		for village_id in self.village:
			self.subscribe(i['id'], village_id)
			if village_id != id:
				self.subscribe(village_id, i['id'])
		for well_id in self.well:
			self.subscribe(i['id'], well_id)
		i['name'] = village_name()
		i['grain'] = 50
		i['water'] = 50
		i['water_packs'] = 0
		i['free_water_packs'] = 0
		i['waste'] = 0
		i['kwacha'] = 0
		i['huts'] = 0
		i['fields'] = 0
		i['free_fields'] = 0
		i['build_material'] = 0
		i['last_action'] = self.time + 60 * 120 # Give the user some time to figure out what's going on
		i['x'] = random.randint(-750, 750)
		i['y'] = random.randint(-750, 750)
		return i
	
	def create_man(self, owner):
		i = self.create('man', owner)
		i['max_health'] = i['health'] = 10
		i['name'] = person_name()
		i['state'] = None
		i['sick'] = False
		return i
	
	def create_woman(self, owner):
		i = self.create('woman', owner)
		i['max_health'] = i['health'] = 8
		i['name'] = person_name()
		i['water_pack'] = False
		i['state'] = None
		i['in_labor'] = False
		i['sick'] = False
		return i
	
	def create_well(self, owner, complete = 0):
		i = self.create('well', owner)
		for village_id in self.village:
			self.subscribe(village_id, i['id'])
		i['name'] = 'Well Site {0}'.format(hex(self.well_index)[2:].upper())
		self.well_index += 1
		i['x'] = random.randint(-750, 750)
		i['y'] = random.randint(-750, 750)
		i['queue'] = []
		i['complete'] = complete # 0 to 100
		i['contamination'] = 0 # 0 to 100
		return i
	
	def create_child(self, owner):
		i = self.create('child', owner)
		i['max_health'] = i['health'] = 5
		i['name'] = person_name()
		i['water_pack'] = False
		i['state'] = None
		i['sick'] = False
		return i
	
	def create(self, klass, owner, id = None):
		if id is None:
			id = uuid.uuid4().hex
		i = { 'owner': owner, 'type': klass, 'id': id }
		if owner is not None:
			self.subscribe(owner, id)
		getattr(self, klass)[id] = i
		self.all[id] = i
		return i
	
	def subscribe(self, user, id):
		subscriptions = self.user_to_object_subscription.get(user)
		if subscriptions is None:
			subscriptions = self.user_to_object_subscription[user] = []
		if id not in subscriptions:
			subscriptions.append(id)

		subscriptions = self.object_to_user_subscription.get(id)
		if subscriptions is None:
			subscriptions = self.object_to_user_subscription[id] = []
		if user not in subscriptions:
			subscriptions.append(user)
	
	def unsubscribe(self, user, id):
		subscriptions = self.user_to_object_subscription[user]
		subscriptions.remove(id)
		if len(subscriptions) == 0:
			del self.user_to_object_subscription[user]

		subscriptions = self.object_to_user_subscription[id]
		if user in subscriptions:
			subscriptions.remove(user)
		if len(subscriptions) == 0:
			del self.object_to_user_subscription[id]
	
	def get_user_subscribed_object_ids(self, user):
		return list(self.user_to_object_subscription.get(user, []))
	
	def get_subscribed_user_ids(self, id):
		return list(self.object_to_user_subscription.get(id, []))
	
	def delete(self, object_id):
		i = self.all[object_id]
		del self.all[object_id]
		del getattr(self, i['type'])[object_id]
		
		subscribed_users = self.object_to_user_subscription.get(object_id)
		if subscribed_users is not None:
			for user_id in subscribed_users:
				user_subscriptions = self.user_to_object_subscription[user_id]
				user_subscriptions.remove(object_id)
				if len(user_subscriptions) == 0:
					del self.user_to_object_subscription[user_id]
			del self.object_to_user_subscription[object_id]
