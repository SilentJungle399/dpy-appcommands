from types import FunctionType
from .enums import MessageFlags
from typing import Coroutine, Dict, List, Optional, Tuple
from discord.ext import commands
import discord
from discord import ui
from discord.ui.item import Item

class InteractionContext:
	bot: commands.Bot
	client: 'SlashClient'
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

	async def reply(
		self, 
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		flags: MessageFlags = None,
		view: ui.View = None
	) -> dict:
		...

	async def edit(
		self, 
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		flags: MessageFlags = None,
		view: ui.View = None
	) -> dict:
		...

	async def follow(
		self, 
		content: str = None, *, 
		tts: bool = False,
		embed: discord.Embed = None,
		allowed_mentions = None,
		flags: MessageFlags = None,
		view: ui.View = None
	) -> dict:
		...

	async def delete(self) -> None:
		...

class SlashCommand:
	client: 'SlashClient'
	name: str
	description: str
	options: dict
	guild: Optional[int]
	options: Optional[List['Option']]
	callback: Optional[FunctionType]

	def from_dict(self, data: dict) -> 'SlashCommand':
		...

	def callback(self, ctx: InteractionContext):
		...

	def register(self):
		...

class SlashClient:
	bot: commands.Bot
	_listeners: Dict[str, SlashCommand]
	_views: Dict[str, Tuple[ui.View, Item]]

	async def get_commands(self) -> List['SlashCommand']:
		...

	async def add_command(self, command: SlashCommand):
		...

	def log(self, message: str):
		...

class Option:
	name: str
	description: Optional[str]
	type: Optional[str]
	required: Optional[bool]
	choices: Optional[List['Choice']]

class Choice:
	name: str
	value: Optional[str]