import discord

from .enums import MessageFlags

from discord import ui
from types import FunctionType
from discord.ext import commands
from discord.ui.item import Item
from typing import Coroutine, Dict, List, Optional, Tuple, TypedDict, Union


class InteractionContext:
	bot: commands.Bot
	client: 'AppClient'
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
	client: 'AppClient'
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

class AppClient:
	bot: commands.Bot
	_listeners: Dict[str, SlashCommand]
	_views: Dict[str, Tuple[ui.View, Item]]

	async def get_commands(self) -> List['SlashCommand']:
		...

	async def add_command(self, command: SlashCommand):
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

class StoredCommand(TypedDict):
	"""The stored command Type

        Parameters
        ------------
        guild: Union[:class:`~int`, None]
            The guild id of command, None if it is glob
        command: :class:`~appcommands.models.SlashCommand`
            The command itself

        Returns
        --------
        :class:`~dict`
            The json resp"""
	guild: Union[int, None]
	command: SlashCommand

