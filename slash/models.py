
from slash.enums import MessageFlags
from typing import Dict, List
import discord
from discord import http
from discord.ext import commands
from .types import SlashClient
import requests
from discord import ui

class InteractionContext:
	def __init__(self, bot: commands.Bot, client: SlashClient) -> None:
		self.bot: commands.Bot = bot
		self.client: SlashClient = client
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
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		ephemeral: bool = False,
		view: ui.View = None
	):
		ret = {
			"content": content,
		}

		if ephemeral:
			ret["flags"] = 64

		if embed:
			ret["embeds"] = [embed.to_dict()]

		if view:
			ret["components"] = view.to_components()
			for i in view.children:
				if i._provided_custom_id:
					self.client._views[i.custom_id] = [view, i]

		url = f"https://discord.com/api/v9/interactions/{self.id}/{self.token}/callback"

		json = {
			"type": 4,
			"data": ret
		}

		resp = requests.post(url, json=json)

		self.client.log(f"Reply response - {resp.status_code}")

		return resp.text

	async def follow(
		self, 
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		ephemeral: bool = False,
		view: ui.View = None
	):
		ret = {
			"content": content,
		}

		if ephemeral:
			ret["flags"] = 64

		if embed:
			ret["embeds"] = [embed.to_dict()]

		if view:
			ret["components"] = view.to_components()
			for i in view.children:
				if i._provided_custom_id:
					self.client._views[i.custom_id] = [view, i]

		url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}"

		resp = requests.post(url, json = ret)

		self.client.log(f"Follow msg response - {resp.status_code}")

		return resp.text

	async def edit(
		self, 
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		ephemeral: bool = False,
		view: ui.View = None
	):
		ret = {
			"content": content,
		}

		if ephemeral:
			ret["flags"] = 64

		if embed:
			ret["embeds"] = [embed.to_dict()]

		if view:
			ret["components"] = view.to_components()
			for i in view.children:
				if i._provided_custom_id:
					self.client._views[i.custom_id] = [view, i]

		url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}/messages/@original"

		resp = requests.patch(url, json=ret)

		self.client.log(f"Reply edit response - {resp.status_code}")

	async def delete(self):
		url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}/messages/@original"

		resp = requests.delete(url)

		self.client.log(f"Delete reply response - {resp.status_code}")

		return resp.text

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
		self.default_permission = data["default_permission"]
		self.type = int(data["type"])
		if "description" in data:
			description = data["description"]
		else:
			description = None
		if "options" in data:
			options = data["options"]
		else:
			options = []

		return self(client, name = data["name"], description = description, options = options)

	def ret_dict(self) -> dict:
		ret = {
			"name": self.name,
			"description": self.description,
			"options": self.options
		}

		return ret

	async def callback(self, ctx: InteractionContext):
		pass
