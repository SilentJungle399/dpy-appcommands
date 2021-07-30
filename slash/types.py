from typing import Coroutine, List
from discord.ext import commands
import discord

class InteractionContext:
	bot: commands.Bot
	version: int
	type: int
	token: str
	id: int
	data: dict
	application_id: int
	member: discord.Member
	channel: discord.TextChannel
	guild: discord.Guild

	def from_dict(self, data: dict) -> 'InteractionContext':
		...

class SlashCommand:
	name: str
	options: dict
	client: 'SlashClient'

	def from_dict(self, data: dict) -> 'SlashCommand':
		...

	def callback(self, ctx: InteractionContext):
		...

	def register(self):
		...

class SlashClient:
	bot: commands.Bot
	_listeners: dict

	async def get_commands(self) -> List['SlashCommand']:
		...

	async def add_command(self, command: SlashCommand):
		...