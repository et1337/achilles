import uuid
import random
import data

def village_name():
	return random.choice(data.villages)

def person_name():
	return '{0} {1}'.format(random.choice(data.names), random.choice(data.names))

class State(object):
	def __init__(self):
		self.all = {}
		self.village = {}
		self.field = {}
		self.water_pack = {}
		self.hut = {}
		self.man = {}
		self.woman = {}
		self.child = {}
	
	def create_village(self, id = None):
		if id is None:
			id = uuid.uuid4().hex
		i = { 'id': id, 'owner': None }
		self.all[id] = i
		self.village[id] = i
		i['name'] = village_name()
		i['food'] = 50
		i['water'] = 50
		i['waste'] = 0
		return i
	
	def create_field(self, owner):
		return self.create('field', owner)
	
	def create_water_pack(self, owner):
		return self.create('water_pack', owner)
	
	def create_hut(self, owner):
		return self.create('hut', owner)
	
	def create_man(self, owner):
		i = self.create('man', owner)
		i['health'] = 10
		i['awake'] = True
		i['name'] = person_name()
		return i
	
	def create_woman(self, owner):
		i = self.create('woman', owner)
		i['health'] = 8
		i['awake'] = True
		i['name'] = person_name()
		return i
	
	def create_child(self, owner):
		i = self.create('child', owner)
		i['health'] = 5
		i['awake'] = True
		i['name'] = person_name()
		return i
	
	def create(self, klass, owner):
		id = uuid.uuid4().hex
		i = { 'owner': owner, 'type': klass, 'id': id }
		getattr(self, klass)[id] = i
		self.all[id] = i
		return i
	
	def delete(self, i):
		self.all.remove(i['id'])
		getattr(self, i['type']).remove(i['id'])
