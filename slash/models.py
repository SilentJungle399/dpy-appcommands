from slash.enums import MessageFlags
from typing import Dict, List, Union
import discord
from discord import http
from discord.ext import commands
from .types import SlashClient
import requests
from discord import ui
import asyncio

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
        self.user: Union[discord.Member, discord.User] = None
        self.channel: discord.TextChannel = None
        self.guild: discord.Guild = None

    async def from_interaction(self, interaction) -> 'InteractionContext':
        self.version = interaction.version
        self.type = interaction.type
        self.token = interaction.token
        self.id = interaction.id
        self.data = interaction.data
        self.application_id = interaction.application_id
        self.user = interaction.user
        self.guild = None

        if isinstance(interaction.user, discord.Member):
            self.guild = self.user.guild
            
        if interaction.channel_id is not None:
            self.channel = self.guild.get_channel(interaction.channel_id) or await self.guild.fetch_channel(interaction.channel_id)
            if not self.channel:
                self.channel = self.bot.get_channel(interaction.channel_id) or await self.bot.fetch_channel(interaction.channel_id)

        
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

class Option:
    def __init__(self, name: str, description: str, type: int = 3, required: bool = True):
        if type not in (3,4,5,6,7,8,9,10):
            raise ValueError("type should be one of the values (3,4,5,6,7,8,9,10) not {}".format(optype))
        self.name = name
        self.description = description
        self.type = type
        self.required = True

    def ret_dict(self):
        return {"name": self.name,"description": self.description,"type": self.type,"required": self.required}


class SlashCommand:
    def __init__(self, client: SlashClient, name: str, description: str, options: List[Option] = [], callback = None, extras: dict = {}):
        if callback is not None:
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or callback.__name__
            callback.__slash_command__ = self
            self.callback = callback
        else:
            self.name = name
        self.client = client
        self._extras = extras
        self.options = options
        self.description = description or ""

    def __repr__(self):
        return "<SlashCommmand name={0} description={1.description}>".format(self.name, self)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_dict(self, client: SlashClient, data: dict) -> 'SlashCommand':
        self.version = int(data["version"])
        self.application_id = int(data["application_id"])
        self.id = int(data["id"])
        self.name = data["name"]
        self.default_permission = data["default_permission"]
        self.type = int(data["type"]) if data.get("type", None) is not None else None
        if "description" in data:
            description = data["description"]
        else:
            description = None
        if "options" in data:
            options = list(Option(**option) for option in data["options"])
        else:
            options = []

        return self(client, name = data["name"], description = description, options = options)

    def ret_dict(self) -> dict:
        ret = {
            "name": self.name,
            "description": self.description,
            "options": list(d.ret_dict() for d in self.options)
        }
        ret = {**ret, **self._extras}
        return ret

    def subcommand(self, *args,**kwargs):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('Callback must be a coroutine.')
            result = SlashCommand(self.slashclient, *args, **kwargs, callback=func, extras={"type": 1})
            result.client.bot.loop.create_task(result.client.add_command(result))
            return result
        return wrapper

    def group(self, *args,**kwargs):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('Callback must be a coroutine.')
            result = SlashCommand(self.slashclient, *args, **kwargs, callback=func, extras={"type": 2})
            result.client.bot.loop.create_task(result.client.add_command(result))
            return result
        return wrapper

    async def callback(self, ctx: InteractionContext):
        raise NotImplementedError


def command(*args,**kwargs):
    def wrapper(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')
        result = SlashCommand(*args, **kwargs, callback=func)
        result.client.bot.loop.create_task(result.client.add_command(result))
        return result
    return wrapper
