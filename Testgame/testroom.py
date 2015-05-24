firstrun = True

def onenter(api, variables, inventory, items):
	""" List items? """
	global firstrun
	print "New room?!?" if firstrun else "You have been here before. At least you think so."
	firstrun = False

	print variables, inventory, items
	return variables, inventory, items
def oncommand(api, command, variables, inventory, items):
	""" Process command """
	print items
	if len(items)>0:
		print "You gain posession of "+items[0]+"."
		inventory.append(items[0])
		del items[0]
		return True, variables, inventory, items
	if command == "test":
		api("testroom.xml:doors:north:locked:1")

	return False, variables, inventory, items
