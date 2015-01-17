import uuid
import random
import data

def village_name():
	return random.choice(data.villages)

def person_name():
	return '{0} {1}'.format(random.choice(data.names), random.choice(data.names))

class State(object):
	def __init__(self, time_scale):
		self.time_scale = time_scale
		self.time = 0
		self.all = {}
		self.village = {}
		self.water_pack = {}
		self.man = {}
		self.woman = {}
		self.child = {}
	
	def create_village(self, id = None):
		i = self.create('village', None, id)
		i['name'] = village_name()
		i['grain'] = 50
		i['water'] = 50
		i['waste'] = 0
		i['kwacha'] = 0
		i['huts'] = 0
		i['fields'] = 0
		return i
	
	def create_water_pack(self, owner):
		return self.create('water_pack', owner)
	
	def create_man(self, owner):
		i = self.create('man', owner)
		i['health'] = 10
		i['awake'] = True
		i['name'] = person_name()
		i['age'] = random.randint(13, 75)
		return i
	
	def create_woman(self, owner):
		i = self.create('woman', owner)
		i['health'] = 8
		i['awake'] = True
		i['name'] = person_name()
		i['age'] = random.randint(13, 75)
		return i
	
	def create_child(self, owner):
		i = self.create('child', owner)
		i['health'] = 5
		i['awake'] = True
		i['name'] = person_name()
		i['age'] = random.randint(3, 12)
		return i
	
	def create(self, klass, owner, id = None):
		if id is None:
			id = uuid.uuid4().hex
		i = { 'owner': owner, 'type': klass, 'id': id }
		getattr(self, klass)[id] = i
		self.all[id] = i
		return i
	
	def delete(self, i):
		self.all.remove(i['id'])
		getattr(self, i['type']).remove(i['id'])
