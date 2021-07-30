from typing import Coroutine
from .models import *
from .exceptions import *
from discord import http
from discord.ext import commands

class SlashClient:
	def __init__(self, bot: commands.Bot) -> None:
		self.bot: commands.Bot = bot
		self._listeners = {}
		self.bot.add_listener(self.socket_resp, "on_socket_response")

	async def socket_resp(self, data):
		if data["t"] == "INTERACTION_CREATE":
			if data['d']['data']['name'] in self._listeners:
				context = await InteractionContext(self.bot).from_dict(data['d'])
				await (self._listeners[context.data["name"]]).callback(context)

	async def get_commands(self) -> List[SlashCommand]:
		data = await self.bot.http.request(
			route = http.Route(
				"GET",
				f"/applications/{self.bot.user.id}/commands"
			)
		)
		ret = []
		for i in data:
			ret.append(SlashCommand.from_dict(self, i))

		return ret

	async def add_command(self, command: SlashCommand):
		slashcmds = await self.get_commands()
		if command.name in self._listeners:
			raise CommandExists(f"Command {command.name} has already been registered!")
		else:
			self._listeners[command.name] = command

			checks = list(map(lambda a: a.name, slashcmds))
			
			if command.name not in checks:
				await self.bot.http.request(
					route = http.Route("POST", f"/applications/{self.bot.user.id}/commands"),
					json = command.ret_dict()
				)

	async def remove_command(self, name: str):
		slashcmds = await self.get_commands()
		checks = list(map(lambda a: a.name, slashcmds))
		id = slashcmds[checks.index(name)].id

		await self.bot.http.request(
			route = http.Route("DELETE", f"/applications/{self.bot.user.id}/commands/{id}")
		)
