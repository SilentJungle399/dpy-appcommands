
from typing import Dict, List
import discord
from discord.ext import commands
from .types import SlashClient

class InteractionContext:
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot
		self.version: int = None
		self.type: int = None
		self.token: str = None
		self.id: int = None
		self.data: dict = None
		self.application_id: int = None
		self.member: discord.Member = None
		self.channel: discord.TextChannel = None
		self.guild: discord.Guild = None

	async def from_dict(self, data: dict) -> 'InteractionContext':
		self.version = data["version"]
		self.type = data["type"]
		self.token = data["token"]
		self.id = int(data["id"])
		self.data = data["data"]
		self.application_id = int(data["application_id"])

		if "guild" in data:
			self.guild = self.bot.get_guild(int(data["guild_id"]))
			if not self.guild:
				self.guild = await self.bot.fetch_guild(int(data["guild_id"]))

		if "channel" in data:
			self.channel = self.guild.get_channel(int(data["channel_id"]))
			if not self.channel:
				self.channel = await self.guild.fetch_channel(int(data["channel_id"]))

		if "member" in data:
			self.member = self.guild.get_member(int(data["member"]["user"]["id"]))
			if not self.member:
				self.member = await self.guild.fetch_member(int(data["member"]["user"]["id"]))

		return self

class SlashCommand:
	def __init__(self, client: SlashClient, name: str, options: List[Dict]):
		self.client = client
		self.name = name
		self.options = options

	def from_dict(self, data: dict) -> 'SlashCommand':
		self.version = int(data["version"])
		self.application_id = int(data["application_id"])
		self.id = int(data["id"])
		self.name = data["name"]
		self.description = data["description"]
		self.default_permission = data["default_permission"]
		self.type = int(data["type"])
		self.options = data["options"]

		return self

	async def callback(self, ctx: InteractionContext):
		pass

	def register(self):
		self.client.add_command(self)