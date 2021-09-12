import copy
import typing
import discord
import asyncio
import inspect
import functools

from .utils import *
from .types import AppClient
from .enums import OptionType

from discord import ui
from discord import http
from discord.ext import commands
from aiohttp.client import ClientSession
from typing import Dict, List, Union, Optional, Coroutine, Callable


__all__ = (
    "Choice",
    "command",
    "InteractionContext",
    "InteractionData",
    "Option",
    "SlashCommand"
)

async def get_ctx_kw(ctx, params):
    bot, cmd, kwargs = ctx.bot, ctx.command, {}
    if cmd is not None and len(ctx.data.options) > 0:
        for k, _ in params.items():
            for opt in ctx.data.options:    
                if k == opt.name:
                    if opt.type == OptionType.USER:
                        if ctx.guild:
                            value = ctx.guild.get_member(opt.value) or await ctx.guild.fetch_member(opt.value)
                        else:
                            value = bot.get_user(opt.value) or await bot.fetch_user(opt.value)
                    elif opt.type == OptionType.CHANNEL:
                        if ctx.guild:
                            value = ctx.guild.get_channel(opt.value) or await ctx.guild.fetch_channel(opt.value)
                        else:
                            value = bot.get_channel(opt.value) or await bot.fetch_channel(opt.value)
                    elif opt.type == OptionType.ROLE:
                        value = ctx.guild.get_role(opt.value)
                    elif opt.type == OptionType.MENTIONABLE:
                        value = discord.Object(opt.value)
                    else:
                        value = opt.value
                    kwargs[k] = value
    return kwargs

def unwrap_function(function):
    partial = functools.partial
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__
        elif isinstance(function, partial):
            function = function.func
        else:
            return function


def get_signature_parameters(function, globalns):
    signature = inspect.signature(function)
    params = {}
    cache = {}
    eval_annotation = discord.utils.evaluate_annotation
    for name, parameter in signature.parameters.items():
        annotation = parameter.annotation
        if annotation is parameter.empty:
            params[name] = parameter
            continue
        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)

        params[name] = parameter.replace(annotation=annotation)

    return params


def generate_options(function, description: str = "No description."):
    options = []
    params = iter(inspect.signature(function).parameters.values())
    if next(params).name in ("self", "cls"):
        # Skip 1. (+ 2.) parameter, self/cls and ctx
        next(params)

    for param in params:
        required = True
        if isinstance(param.annotation, str):
            # if from __future__ import annotations, then annotations are strings and should be converted back to types
            param = param.replace(
                annotation=eval(param.annotation, function.__globals__))

        if param.default is not inspect._empty:
            required = False
        elif getattr(param.annotation, "__origin__", None) is typing.Union:
            # Make a command argument optional with typing.Optional[type] or typing.Union[type, None]
            args = getattr(param.annotation, "__args__", None)
            if args:
                param = param.replace(annotation=args[0])
                required = not isinstance(args[-1], type(None))

        if isinstance(param.annotation, Option):
            kw=param.annotation.to_dict()
            kw["name"] = param.name
            options.append(Option.from_dict(kw))
        else:
            option_type = (OptionType.from_type(param.annotation)
                           or OptionType.STRING)
            name = param.name
            options.append(
                Option(name, description or "No description", option_type,
                       required))

    return options


class InteractionContext:
    """The ctx param given in CMD callbacks
    
    **Attributes**

    Attributes
    ------------
    bot: Union[:class:`~discord.ext.commands.Bot`, :class:`~discord.ext.commands.AutoShardedBot`]
        The discord bot
    client: :class:`~appcommands.client.AppClient`
        The appclient on which this context is used 
    type: :class:`~int`
        Interaction type 
    guild: Union[:class:`~discord.Guild`, None]
        The guild in which command is fired, None if it is in DMs 
    channel: Union[:class:`~discord.TextChannel`, :class:`~discord.DMChannel`]
        The channel in which command is triggered
    id: :class:`~int`
        id of this interaction
    user: Union[:class:`~discord.User`, :class:`~discord.Member`]
        The user who fired this cmd 
    token: :class:`~str`
        token of this interaction, (valid for 15 mins)"""
    def __init__(self, bot: commands.Bot, client: AppClient) -> None:
        self.bot: commands.Bot = bot
        self.client: AppClient = client
        self.__session: ClientSession = self.bot.http._HTTPClient__session
        self.version: int = None
        self.type: int = None
        self.token: str = None
        self.id: int = None
        self.data: InteractionData = None
        self.application_id: int = None
        self.user: Union[discord.Member, discord.User] = None
        self.channel: discord.TextChannel = None
        self.guild: discord.Guild = None
        self.kwargs: dict = {}

    async def from_interaction(self, interaction) -> 'InteractionContext':
        self.version = interaction.version
        self.type = interaction.type
        self.token = interaction.token
        self.id = interaction.id
        self.data = InteractionData.from_dict(interaction.data)
        cmd = self.bot.appclient.commands.get(self.data.id, None)['command']
        self.command = cmd
        params = copy.deepcopy(cmd.params)
        if cmd.cog and str(list(params.keys())[0]) in ("cls", "self"): # cls/self only
            params.pop(list(params.keys())[0])
        self.kwargs[str(list(params.keys())[0])] = self
        params.pop(str(list(params.keys())[0]))
        self.application_id = interaction.application_id
        self.user = self.author = interaction.user
        self.guild = None

        if isinstance(interaction.user, discord.Member):
            self.guild = self.user.guild

        if interaction.channel_id is not None and self.guild:
            self.channel = self.guild.get_channel(
                interaction.channel_id) or await self.guild.fetch_channel(
                    interaction.channel_id)
        elif interaction.channel_id is not None:
            self.channel = await self.user._get_channel()

        self.kwargs = {**self.kwargs, **(await get_ctx_kw(self, params))}
        return self

    async def reply(self,
                    content: str = None,
                    *,
                    tts: bool = False,
                    embed: discord.Embed = None,
                    allowed_mentions=None,
                    ephemeral: bool = False,
                    view: ui.View = None):
        """Replies to given interaction"""
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

        json = {"type": 4, "data": ret}

        async with self.__session.request('POST', url, json = json) as response:
            self.client.log(f"Reply response - {response.status}")

            return response.text

    async def follow(self,
                     content: str = None,
                     *,
                     tts: bool = False,
                     embed: discord.Embed = None,
                     allowed_mentions=None,
                     ephemeral: bool = False,
                     view: ui.View = None):
        """Sends a follow-up message."""
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

        async with self.__session.request('POST', url, json = ret) as response:
            self.client.log(f"Follow msg response - {response.status}")

            return response.text

    async def edit(self,
                   content: str = None,
                   *,
                   tts: bool = False,
                   embed: discord.Embed = None,
                   allowed_mentions=None,
                   view: ui.View = None):
        """edit the responded msg"""
        ret = {
            "content": content,
        }

        if embed:
            ret["embeds"] = [embed.to_dict()]

        if view:
            ret["components"] = view.to_components()
            for i in view.children:
                if i._provided_custom_id:
                    self.client._views[i.custom_id] = [view, i]

        url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}/messages/@original"

        async with self.__session.request('PATCH', url, json = ret) as response:
            self.client.log(f"Reply edit response - {response.status}")

    async def delete(self):
        """Delete the responded msg"""
        url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}/messages/@original"

        async with self.__session.request('DELETE', url) as response:
            self.client.log(f"Delete reply response - {response.status}")

            return response.text

    async def defer(self, ephemeral: bool = False):
        """Defers the interaction so discord knows bot has recieved it, this is considered a reply so you must edit it later."""
        url = f"https://discord.com/api/v9/interactions/{self.id}/{self.token}/callback"
        ret = {"type": 5}
        if ephemeral:
            ret["data"] = {"flags": 64}

        async with self.__session.request('POST', url, json=ret) as response:
            self.client.log(f"Deferred interaction - {response.status}")

            return response.text

class InteractionData:
    """The data given in `ctx.data`

    **Attributes**

    Attributes
    ------------
    type: :class:`~int`
        Type of the command
    name: :class:`~str`
        Name of the command
    id: :class:`~int`
        Id of the command
    options: List[:class:`~appcommands.models.Option`]
        Options passed in command
    """
    def __init__(self, type: int, name: str, _id: int, options: Optional[List['Option']] = None) -> None:
        self.type = type
        self.name = name
        self.id = int(_id)
        self.options = options

    def __repr__(self):
        return f"<InteractionData type={self.type} id={self.id} name={self.name} options={self.options}>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_dict(cls, d: dict) -> 'InteractionData':
        options = []
        if d.get('options'):
            for i in d.get('options'):
                options.append(Option.from_dict(i))

        return cls(d['type'], d['name'], d['id'], options)

class Choice:
    """Choice for the option value 
    
    Parameters 
    ------------
    name: :class:`~str`
        name of the choice, (required)
    value: Optional[:class:`~str`]
        value of the choice used for backends, (optional)"""
    def __init__(self, name: str, value: Optional[str] = None):
        self.name = name
        self.value = value or self.name

    def to_dict(self):
        return {"name": self.name, "value": self.value}

    def __repr__(self):
        return "<Choice name={0} value={1.value}>".format(self.name, self)


class Option:
    """Options for slashcommands 
    
    Parameters 
    ------------
    name: :class:`~str`
        name of the Option, (required)
    description: Optional[:class:`~str`]
        description of option, (optional)
    type: Optional[:class:`~int`]
        the type of option, (optional)
    required: Optional[:class:`~bool`]
        whether the option is required
    choices: Optional[List[:class:`~appcommands.models.Choice`]]
        The choices for this option
    """
    def __init__(self,
                 name: str,
                 description: Optional[str] = "No description.",
                 type: Optional[int] = 3,
                 required: Optional[bool] = True,
                 value: str = None,
                 choices: Optional[List[Choice]] = []):
        if type not in (3, 4, 5, 6, 7, 8, 9, 10):
            raise ValueError(
                "type should be one of the values (3,4,5,6,7,8,9,10) not {}".
                format(type))
        self.name = name
        self.description = description
        self.type = type
        self.choices = choices
        self.value = value
        self.required = required

    def to_dict(self):
        ret = {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "choices": list(c.to_dict() for c in self.choices),
            "required": self.required,
            "value": self.value
        }
        return ret

    @classmethod
    def from_dict(cls, data):
        required = True if data.get("required") else False
        name = data.get("name")
        description = data.get("description")
        value = data.get("value")
        type = data.get("type")
        choices = []
        if data.get("choices"):
            for choice in data.get('choices'):
                choices.append(Choice(**choice))
        return cls(name, description, type, required, value, choices)

    def __repr__(self):
        return f"<Option name={self.name} description={self.description} type={self.type} required={self.required} value={self.value} choices={self.choices}>"


class SubCommand:
    def __init__(self,
                 client: AppClient,
                 name: str = None,
                 description: str = "No description.",
                 options: List[Option] = [],
                 callback=None,
                 parent=None):
        self.options = options
        if callback is not None:
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or callback.__name__
            self.callback = callback
            unwrap = unwrap_function(callback)
            try:
                globalns = unwrap.__globals__
            except:
                globalns = {}
            self.params = get_signature_parameters(callback, globalns)
            if not options:
                self.options = generate_options(self.callback, description)
        else:
            if not name:
                raise ValueError("You must specify name when callback is None")
            self.name = name

        self.client = client
        self.description = description

    def to_dict(self):
        ret = {
            "name": self.name,
            "description": self.description,
            "options": list(o.to_dict() for o in self.options),
            "type": 1
        }
        return ret

    @classmethod
    def from_dict(self, client: AppClient, data: dict):
        name = data.get("name")
        if "description" in data:
            description = data["description"]
        else:
            description = None
        options = []
        if data.get("options"):
            for opt in data["options"]:
                options.append(Option.from_dict(opt))
        else:
            options = []

        return self(client,
                    name=data.get("name"),
                    description=description,
                    options=options)

    async def callback(self, *args, **kwargs):
        raise NotImplementedError


class SubCommandGroup:
    def __init__(self,
                 client: AppClient,
                 name: str = None,
                 description: str = "No description.",
                 options: List[Option] = [],
                 callback=None,
                 subcommands: List[SubCommand] = []):
        self.options = options
        if callback is not None:
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or callback.__name__
            self.callback = callback
            unwrap = unwrap_function(callback)
            try:
                globalns = unwrap.__globals__
            except:
                globalns = {}
            self.params = get_signature_parameters(callback, globalns)
            if not options:
                self.options = generate_options(self.callback, description)
        else:
            if not name:
                raise ValueError("You must specify name when callback is None")
            self.name = name

        self.client = client
        self.description = description

        self.subcommands = subcommands
        self.options.extend(self.subcommands)

    def to_dict(self):
        ret = {
            "name": self.name,
            "description": self.description,
            "options": list(o.to_dict() for o in self.options),
            "type": 2
        }
        return ret

    @classmethod
    def from_dict(self, client: AppClient, data: dict):
        self.name = data["name"]
        self.type = int(data["type"]) if data.get("type",
                                                  None) is not None else None
        if "description" in data:
            description = data["description"]
        else:
            description = None
        subcommands = []
        options = []
        if data.get("options"):
            for opt in data["options"]:
                if opt["type"] == 1:
                    subcommands.append(SubCommand.from_dict(client, opt))
                else:
                    options.append(Option.from_dict(opt))
        else:
            options = []

        return self(client,
                    name=data["name"],
                    description=description,
                    options=options,
                    subcommands=subcommands)

    async def callback(self, *args, **kwargs):
        raise NotImplementedError


class SlashCommand:
    """SlashCmd base class 
    
    Parameters
    ------------
    client: :class:`~appcommands.client.AppClient`
       Your AppClient instance, (required)
    name: :class:`~str`
       Name of the cmd, (required)
    description: Optional[:class:`~str`]
       description of the cmd, (optional)
    guild: Optional[:class:`~str`]
       id of the guild for which command is to be added, (optional)
    options: Optional[List[:class:`~appcommands.models.Option`]]
       options for your command, (optional)
    callback: Optional[Coroutine]
       the callback which is to be called when a command fires, (optional)
       
    Raises 
    --------
    TypeError 
        Callback is not coroutine 
    ValueError 
        Name not given when coroutine not given
    """
    def __init__(self,
                 client: AppClient,
                 name: str = None,
                 description: Optional[str] = "No description.",
				 guild: Optional[int] = None,
                 options: Optional[List[Option]] = [],
                 callback: Optional[Coroutine] = None,
                 subcommands: Optional[List[Union[SubCommandGroup,
                                                  SubCommand]]] = []) -> None:
        self.options = options
        self.client = client
        self.description = description
        self.guild = guild
        self.cog = None
        if callback:
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or callback.__name__
            unwrap = unwrap_function(callback)
            try:
                globalns = unwrap.__globals__
            except:
                globalns = {}

            self.params = get_signature_parameters(callback, globalns)
            if not options or options == []:
                self.options = generate_options(callback, description)
            self.callback = callback
        elif (hasattr(self, 'callback') and self.callback is not MISSING):
            if not callback:
                callback = self.callback
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or self.__class__.__name__
            unwrap = unwrap_function(callback)
            try:
                globalns = unwrap.__globals__
            except:
                globalns = {}

            self.params = get_signature_parameters(callback, globalns)
            if not options:
                self.options = generate_options(self.callback, description)
        else:
            if not name:
                raise ValueError("You must specify name when callback is None")
            self.name  = name
        self.options.extend(subcommands)

    def __repr__(self):
        return f"<SlashCommmand name='{self.name}' description='{self.description}'>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_dict(self, client: AppClient, data: dict) -> 'SlashCommand':
        self.version = int(data["version"])
        self.application_id = int(data["application_id"])
        self.id = int(data["id"])
        self.name = data["name"]
        self.default_permission = data["default_permission"]
        self.type = int(data["type"]) if data.get("type",
                                                  None) is not None else None
        if "description" in data:
            description = data["description"]
        else:
            description = None
        subcommands = []
        options = []
        if data.get("options"):
            for opt in data["options"]:
                if opt["type"] == 1:
                    subcommands.append(SubCommand.from_dict(client, opt))
                elif opt["type"] == 2:
                    subcommands.append(SubCommandGroup.from_dict(client, opt))
                else:
                    options.append(Option(**opt))
        else:
            options = []

        return self(client,
                    name=data["name"],
                    description=description,
                    options=options,
                    subcommands=subcommands)

    def ret_dict(self) -> dict:
        ret = {
            "name": self.name,
            "description": self.description,
            "options": list(d.to_dict() for d in self.options)
        }
        return ret

    @missing
    async def callback(self, ctx: InteractionContext):
        raise NotImplementedError


def command(client: AppClient, *args, cls: SlashCommand = MISSING, **kwargs):
    """The slash commands wrapper 
    
    Parameters
    ------------
    client: :class:`~appcommands.client.AppClient`
        Your appclient instance, (required)
    name: :class:`~str`
        Name of the command, (required)
    description: Optional[:class:`~str`]
        Description of the command, (optional)
    guild: Optional[:class:`~str`]
        Id of the guild for which command is to be added, (optional)
    options: Optional[List[:class:`~appcommands.models.Option`]]
        Options for the command, detects automatically if None given, (optional)
    cls: :class:`~appcommands.models.SlashCommand`
        The custom command class, must be a subclass of :class:`~appcommands.models.SlashCommand`, (optional)

    Example
    ----------
    
    .. code-block:: python3
    
        from appcommands.models import command
        
        @command(bot.appclient, name="hi", description="Hello!")
        async def hi(ctx, user: discord.Member = None):
            user = user or ctx.user
            await ctx.reply(f"Hi {user.mention}")

    Raises
    --------
    TypeError
        The passed callback is not coroutine or it is already a SlashCommand
    """
    if cls is MISSING:
        cls = SlashCommand

    def wrapper(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')
        if hasattr(func, "__slash__") and isinstance(func.__slash__, SlashCommand):
            raise TypeError('Callback is already a slashcommand.')

        result = cls(client,*args, callback=func, **kwargs)
        func.__slash__ = result
        result.client.bot.loop.create_task(result.client.add_command(result))
        return func

    return wrapper
