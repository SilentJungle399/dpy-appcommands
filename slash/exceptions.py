class Error(Exception):
	""" Comman base class """
	pass

class CommandExists(Error):
	""" Fired when another command with same name is registerd """
	pass