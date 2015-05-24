from __future__ import unicode_literals
import imp
import os
import sys
import re
import codecs
from lxml import etree

class API:
	def __init__(self, player, rooms):
		self.player = player
		self.rooms = rooms
	def request(self, req):
		print "request:", req
		req = req.split(":")
		# toggle door `file.xml:doors:north:locked:0`
		if len(req) == 5 and req[1] == "doors" and req[3] == "locked":
			r = rooms.find_room(req[0])
			if r == None:
				print "Invalid api request: '"+(":".join(req))+"'"
				print "Room file not found."
				sys.exit(1)
			if not req[2] in r.get_directions():
				print "Invalid api request: '"+(":".join(req))+"'"
				print "Invalid direction: '"+req[2]+"'"
				sys.exit(1)
			for d in range(len(r.doors)):
				for i in range(len(r.doors[d])):
					if r.doors[d][i][0]=="direction":
						if r.doors[d][i][1] == req[2]:
							for w in range(len(r.doors[d])):
								if r.doors[d][w][0]=="locked":
									r.doors[d][w] = ["locked", str(int(req[4]))]

		else:
			print "Invalid api request: '"+(":".join(req))+"'"
			sys.exit(1)






class Rooms:
	def __init__(self):
		self.rooms = []
	def link(self):
		""" Add pointers to rooms to doors of rooms """
		for room in self.rooms:
			for i in range(len(room.doors)):
				for r2 in self.rooms:
					if r2.file_name == [q for q in room.doors[i] if q[0] == "file"][0][1]:
						room.doors[i].append(["link", r2])
	def find_room(self, file_name):
		for room in self.rooms:
			if room.file_name == file_name:
				return room
		return None

class Room:
	def __init__(self, file_name, name="", description="", doors=[], items=[], script_file=None):
		self.file_name = file_name
		self.name = name
		self.description = description
		self.doors = doors
		self.items = items
		self.script_file = None
		self.script_module = None
		if script_file != None:
			self.script_file = script_file[0][-1]
			self.script_module = imp.load_source("tmp"+str(id(self)), folder_name+self.script_file) # unique id for tmp module
	def at(self, direction):
		for d in self.doors:
			if [i for i in d if i[0] == "direction"][0][1] == direction:
				l = [i for i in d if i[0] == "locked"]
				if l != [] and l[0][1]=="1":
					print "The door is locked."
					return None
				l = [i for i in d if i[0] == "link"]
				if l == []:
					print "Error: Door with no target"
					sys.exit(1)
				else:
					return l[0][1]
		return None
	def get_directions(self):
		return [[a[1] for a in d if a[0]=="direction"][0] for d in self.doors]
	def onenter(self, player):
		print self.script_module, dir(self.script_module)
		if self.script_module != None:
			try:
				x = self.script_module.onenter(api.request, player.variables, player.inventory, self.items)
			except:
				print "Script '"+self.script_file+"' crashed."
				sys.exit(1)
			if x == None or len(x) != 3 or (type(x[0])!=type({}) and type(x[1])!=type([]) and type(x[2])!=type([])):
				print "Script '"+self.script_file+"' returned invalid data."
				sys.exit(1)
			player.variables, player.inventory, self.items = x
	def runcommand(self, command, player):
		if self.script_module != None:
			try:
				x = self.script_module.oncommand(api.request, command, player.variables, player.inventory, self.items)
			except:
				print "Script '"+self.script_file+"' crashed."
				sys.exit(1)
			if x == None or len(x) != 4 or (type(x[1])!=type({}) and type(x[2])!=type([]) and type(x[3])!=type([])):
				print "Script '"+self.script_file+"' returned invalid data."
				sys.exit(1)
			if x[0]:
				player.variables, player.inventory, self.items = x[1:]
			return bool(x[0])
		else:
			return False
	def __repr__(self):
		return "Room<\""+self.name+"\">"

class Player:
	def __init__(self, startroom):
		self.location = startroom
		self.inventory = []
		self.variables = {} # cross-script variables
	def init_later(self):
		self.location.onenter(self)
	def go(self, direction):
		""" Change room """
		n = self.location.at(direction)
		if n == None:
			return False
		self.location = n
		self.location.onenter(self)
		return True
	def runcommand(self, command):
		self.location.runcommand(command, self)


def main():
	global folder_name, api, rooms
	# load game
	folder_name = [i for i in sys.argv[1:] if not i.startswith("-")][0]
	rooms, main_data, startroom = load()

	# init game
	rooms.link()
	player = Player(rooms.find_room(startroom))
	api = API(player, rooms)
	player.init_later()

	# print some info
	if "intro" in main_data.keys():
		print ""
		print main_data["intro"]
	print ""
	print player.location.description
	print ""

	# game loop
	while True:
		try:
			inp = " ".join(raw_input("> ").lower().strip().split())
		except EOFError:
			print "quit game"
			sys.exit(0)

		# regex
		go_direction = re.findall("^(?:go)\\s+("+"|".join(player.location.get_directions())+")$", inp, re.IGNORECASE)

		# compare
		if go_direction != []:
			if player.go(go_direction[0]):
				print ""
				print player.location.description
				print ""
			else:
				print "You can't go there."
		elif inp == "look":
			print ""
			print player.location.description
			print ""
		elif inp == "inventory":
			if player.inventory == []:
				print "Inventory is empty"
			else:
				print "Items in inventory:"
				for i in player.inventory:
					print " * "+str(i)
		else:
			if not player.runcommand(inp):
				print inp+": How's that?"

def load():
	global folder_name
	# generic init
	rooms = Rooms()

	# load gamefiles
	gamefiles = os.listdir(folder_name)
	if not "main.xml" in gamefiles:
		print "Error: Missing 'main.xml'"
		sys.exit(1)

	with codecs.open(os.path.join(folder_name, "main.xml"), "r", "utf-8") as fo:
		contents = fo.read().replace("\r\n", "\n")
	# parse comments
	contents = re.sub("<!--.+?-->", "", contents)
	# parse xml
	root = etree.fromstring(contents)
	if root.tag != "main":
		print "Error: Invalid format: root tag is not 'main'"
		print "In file '"+os.path.join(folder_name, "main.xml")+"'"
		sys.exit(1)
	main_data = {"meta":[]}
	for element in root.iterchildren():
		if element.tag == "meta":
			main_data[element.tag]+=element.items()
		elif element.tag in ["description", "intro"]:
			main_data[element.tag] = "\n".join([" ".join(i.split()) for i in element.text.split("\n") if i.strip() != ""])
		elif element.tag in ["settings"]:
			main_data[element.tag] = []
			for subelement in element.iterchildren():
				if subelement.tag in ["startroom"]:
					main_data[element.tag].append([subelement.tag, subelement.items()])

	for file_name in [i for i in gamefiles if re.findall("[a-zA-Z0-9_]+\\.xml", i)!=[]]:
		if file_name == "main.xml":
			continue
		with codecs.open(os.path.join(folder_name, file_name), "r", "utf-8") as fo:
			contents = fo.read().replace("\r\n", "\n")
		# parse comments
		contents = re.sub("<!--.+?-->", "", contents)
		# parse xml
		root = etree.fromstring(contents)
		if root.tag != "room":
			print "Error: Invalid format: root tag is not 'room'"
			sys.exit(1)
		room_data = {}
		for element in root.iterchildren():
			if element.tag in ["script"]:
				room_data[element.tag] = element.items()
			elif element.tag in ["description"]:
				room_data[element.tag] = "\n".join([" ".join(i.split()) for i in element.text.split("\n") if i.strip() != ""])
			elif element.tag in ["doors", "items"]:
				room_data[element.tag] = []
				for subelement in element.iterchildren():
					if subelement.tag in ["door", "item"]:
						room_data[element.tag].append(subelement.items())
		try:
			doors = []
			if "doors" in room_data.keys():
				doors = room_data["doors"]
			items = []
			if "items" in room_data.keys():
				items = [[i[1] for i in q if i[0] == "name"][0] for q in room_data["items"]]
			script = None
			if "script" in room_data.keys():
				script = room_data["script"]
			rooms.rooms.append(Room(file_name, filter((lambda x: x[0]=="name"), root.items())[0][1], room_data["description"], doors, items, script))
		except:
			print "Error: Invalid room data."
			print "In file '"+os.path.join(folder_name, file_name)+"'"
			sys.exit(1)

	# test data
	if [i for i in main_data["settings"] if i[0] == "startroom"] == []:
		print "Error: Invalid settings: Start room is not defined"
		print "In file '"+os.path.join(folder_name, file_name)+"'"
		sys.exit(1)
	else:
		try:
			startroom = [q for q in [i for i in main_data["settings"] if i[0] == "startroom"][0][1] if q[0] == "file"][0][1]
		except:
			print "Error: Invalid settings: Start room is not defined"
			print "In file '"+os.path.join(folder_name, file_name)+"'"
			sys.exit(1)
	return rooms, main_data, startroom




if __name__=="__main__":
	if len(sys.argv)<2 or "--help" in sys.argv:
		print "Usage: python "+sys.argv[0]+" <Gamefolder>"
		sys.exit()
	main()
