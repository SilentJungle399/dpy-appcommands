
from typing import Dict, List
import discord
from discord import http
from discord.ext import commands
from .types import SlashClient
import requests

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

		if "guild_id" in data:
			self.guild = self.bot.get_guild(int(data["guild_id"]))
			if not self.guild:
				self.guild = await self.bot.fetch_guild(int(data["guild_id"]))

		if "channel_id" in data:
			self.channel = self.guild.get_channel(int(data["channel_id"]))
			if not self.channel:
				self.channel = await self.guild.fetch_channel(int(data["channel_id"]))

		if "member" in data:
			self.member = self.guild.get_member(int(data["member"]["user"]["id"]))
			if not self.member:
				self.member = await self.guild.fetch_member(int(data["member"]["user"]["id"]))

		return self

	async def reply(
		self, 
		content=None, *, 
		tts=False,
		embed=None,
		allowed_mentions=None,
		flags=None
	):

		if embed:
			embed = embed.to_dict()

		url = f"https://discord.com/api/v9/interactions/{self.id}/{self.token}/callback"

		json = {
			"type": 4,
			"data": {
				"content": content,
				"flags": flags
			}
		}

		requests.post(url, json=json)

class SlashCommand:
	def __init__(self, client: SlashClient, name: str = None, options: List[Dict] = None, description: str = None):
		self.client = client
		self.name = name
		self.options = options
		self.description = description

	@classmethod
	def from_dict(self, client: SlashClient, data: dict) -> 'SlashCommand':
		self.version = int(data["version"])
		self.application_id = int(data["application_id"])
		self.id = int(data["id"])
		self.name = data["name"]
		self.description = data["description"]
		self.default_permission = data["default_permission"]
		self.type = int(data["type"])
		self.options = data["options"]

		return self(client, name = data["name"], description = data["description"], options = data["options"])

	def ret_dict(self) -> dict:
		ret = {
			"name": self.name,
			"description": self.description,
			"options": self.options
		}

		return ret

	async def callback(self, ctx: InteractionContext):
		pass