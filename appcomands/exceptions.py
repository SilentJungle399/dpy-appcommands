class Error(Exception):
	"""SlashCommand base class error"""
	pass

class CommandExists(Error):
	""" Fired when another command with same name is registerd """
	pass

class CommandDoesNotExists(Error):
	""" Fired when another command does not exist """
	pass

class CommandNotRegistered(Error):
	""" Fired when the command has not been registered """
	pass

class ExtensionNotFound(Error):
	""" Fired when the Extension was not found """
	pass

class LoadFailed(Error):
	""" Fired when the Extension could not be loaded """
	pass


class ExtensionNotLoaded(Error):
	""" Fired when the Extension couldn't be loaded """
	pass
