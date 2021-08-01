from typing import Coroutine, List, Tuple

from discord.ui.item import Item
from .models import *
from .exceptions import *
from discord import http, ui
from discord.ext import commands
from discord.interactions import Interaction

class SlashClient:
	def __init__(self, bot: commands.Bot, logging: bool = False) -> None:
		self.bot: commands.Bot = bot
		self.logging: bool = logging
		self._listeners = {}
		self._views: Dict[str, Tuple[ui.View, Item]] = {}
		self.bot.add_listener(self.socket_resp, "on_socket_response")

	def log(self, message):
		if self.logging:
			print(message)

	async def socket_resp(self, data):
		if data["t"] == "INTERACTION_CREATE":
			if data['d']['type'] == 2:
				if data['d']['data']['name'] in self._listeners:
					context = await InteractionContext(self.bot, self).from_dict(data['d'])
					await (self._listeners[context.data["name"]]).callback(context)

			elif data['d']['type'] == 3:
				d = data['d']
				interactctx = Interaction(data=d, state=self.bot._connection)
				custom_id = interactctx.data['custom_id']

				view, item = self._views[custom_id]

				item.refresh_state(interactctx)
				view._dispatch_item(item, interactctx)

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
			raise CommandExists(f"Command '{command.name}' has already been registered!")
		else:
			self._listeners[command.name] = command
			self.log(f"Slash command '{command.name}' registered!")

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
