from .enums import MessageFlags
from typing import Dict, List, Union, Optional
import discord
from discord import http
from discord.ext import commands
from .types import SlashClient
from .enums import OptionType
import requests
from discord import ui
import asyncio
import inspect, functools, typing

__all__ = ("InteractionContext", "Option", "SlashCommand", "command", "Choice")


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

        option_type = (OptionType.from_type(param.annotation)
                       or OptionType.STRING)
        name = param.name
        options.append(
            Option(name, description or "No description", option_type,
                   required))

    return options


class InteractionContext:
    """The ctx param given in CMD callbacks
    
    Attributes
    ------------
    bot: Union[:class:`~discord.ext.commands.Bot`,:class:`~discord.ext.commands.AutoShardedBot`]
        The discord bot
    client: :class:`~slash.client.SlashClient`
        The slashclient on which this context is used 
    type: `int`
        Interaction type 
    guild: Union[:class:`~discord.Guild`, None]
        The guild in which command is fired, None if it is in DMs 
    channel: Union[:class:`~discord.TextChannel`, :class:`~discord.DMChannel`]
        The channel in which command is triggered
    id: `int`
        id of this interaction
  user: Union[:class:`~discord.User`,:class:`~discord.Member`]
      The user who fired this cmd 
  token: `str`
      token of this interaction, (valid for 15 mins)"""
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
        self.kwargs: dict = {}

    async def from_interaction(self, interaction) -> 'InteractionContext':
        self.version = interaction.version
        self.type = interaction.type
        self.token = interaction.token
        self.id = interaction.id
        self.data = interaction.data
        cmd = self.bot.slashclient._listeners.get(self.data.get("name"), None)
        if cmd is not None and "options" in self.data:
            for k, v in cmd.params.items():
                for opt in self.data.get("options"):
                    if k == opt.get("name", ""):
                        self.kwargs[k] = opt.get("value", "")
        self.application_id = interaction.application_id
        self.user = interaction.user
        self.guild = None

        if isinstance(interaction.user, discord.Member):
            self.guild = self.user.guild

        if interaction.channel_id is not None and self.guild:
            self.channel = self.guild.get_channel(
                interaction.channel_id) or await self.guild.fetch_channel(
                    interaction.channel_id)
        elif interaction.channel_id is not None:
            self.channel = await self.user._get_channel()

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

        resp = requests.post(url, json=json)

        self.client.log(f"Reply response - {resp.status_code}")

        return resp.text

    async def follow(self,
                     content: str = None,
                     *,
                     tts: bool = False,
                     embed: discord.Embed = None,
                     allowed_mentions=None,
                     ephemeral: bool = False,
                     view: ui.View = None):
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

        resp = requests.post(url, json=ret)

        self.client.log(f"Follow msg response - {resp.status_code}")

        return resp.text

    async def edit(self,
                   content: str = None,
                   *,
                   tts: bool = False,
                   embed: discord.Embed = None,
                   allowed_mentions=None,
                   ephemeral: bool = False,
                   view: ui.View = None):
        """edit he responded msg"""
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
        """Delete the responded msg"""
        url = f"https://discord.com/api/v9/webhooks/{self.application_id}/{self.token}/messages/@original"

        resp = requests.delete(url)

        self.client.log(f"Delete reply response - {resp.status_code}")

        return resp.text


class Choice:
    """Choice for the option value 
    
    Parameters 
    ------------
    name: `str`
        name of the choice, (required)
    value: Optional[`str`]
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
    name: `str`
        name of the Option, (required)
    description: Optional[`str`]
        description of option, (optional)
    type: Optional[`int`]
        the type of option, (optional)
    required: Optional[`bool`]
        whether the option is required
    choices: Optional[List[:class:`~slash.models.Choice`]]
        The choices for this option
    """
    def __init__(self,
                 name: str,
                 description: Optional[str] = "No description.",
                 type: Optional[int] = 3,
                 required: Optional[bool] = True,
                 choices: Optional[List[Choice]] = []):
        if type not in (3, 4, 5, 6, 7, 8, 9, 10):
            raise ValueError(
                "type should be one of the values (3,4,5,6,7,8,9,10) not {}".
                format(type))
        self.name = name
        self.description = description
        self.type = type
        self.choices = choices
        self.required = required

    def to_dict(self):
        ret = {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "choices": list(c.to_dict() for c in self.choices),
            "required": self.required
        }
        return ret

    @classmethod
    def from_dict(cls, data):
        required = data.get("required")
        name = data.get("name")
        description = data.get("description")
        type = data.get("type")
        choices = []
        if data.get("choices"):
            for choice in choices:
                choices.append(Choice(**choice))
        return cls(name, description, type, required, choices)

    def __repr__(self):
        return "<Option name={0.name} description={1} type={2.type} required={3} choices={0.choices}>".format(
            self, self.description, self, self.required)


class SubCommand:
    def __init__(self,
                 client: SlashClient,
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
            callback.__slash_command__ = self
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
        self.full_name = f"{parent} {self.name}"

    def to_dict(self):
        ret = {
            "name": self.name,
            "description": self.description,
            "options": list(o.to_dict() for o in self.options),
            "type": 1
        }
        return ret

    @classmethod
    def from_dict(self, client: SlashClient, data: dict):
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
                 client: SlashClient,
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
            callback.__slash_command__ = self
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
    def from_dict(self, client: SlashClient, data: dict):
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
    
    Prameters
    ------------
    client: :class:`~slash.client.SlashClient`
       Your SlashClient instance, (required)
    name: str
       Name of the cmd, (required)
    description: Optional[`str`]
       description of the cmd, (optional)
    options: Optional[List[:class:`~slash.models.Option`]]
       options for your command, (optional)
    callback: Optional[Coroutine[Callable]]
       the callback which is to be called when a command fires, (optional)
       
    Raises 
    --------
    TypeError 
        Callback is not coroutine 
    ValueError 
        Name not given when coroutine not given
    """
    def __init__(self,
                 client: SlashClient,
                 name: str = None,
                 description: Optional[str] = "No description.",
                 options: Optional[List[Option]] = [],
                 callback=None,
                 subcommands: Optional[List[Union[SubCommandGroup,
                                                  SubCommand]]] = []):
        self.options = options
        if callback is not None:
            if not asyncio.iscoroutinefunction(callback):
                raise TypeError('Callback must be a coroutine.')
            self.name = name or callback.__name__
            callback.__slash_command__ = self
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
        self.description = description or ""
        self.options.extend(subcommands)
        #print(self.options)

    def __repr__(self):
        return "<SlashCommmand name={0} description={1.description}>".format(
            self.name, self)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_dict(self, client: SlashClient, data: dict) -> 'SlashCommand':
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
        ret = {**ret}
        return ret

    async def callback(self, ctx: InteractionContext):
        raise NotImplementedError


def command(*args, **kwargs):
    """The slash commands wrapper 
    
    Parameters
    ------------
    client: :class:`~slash.client.SlashClient`
        Your slashclient instance, (required)
    name: str
        Name of the command, (required)
    description: Optional[`str`]
        Description of the command, (optional)
    options: Optional[List[:class:`~slash.models.Option`]]
        Options for the command, detects automatically if None given, (optional)
        
    Examples
    ----------
    
    .. code-block:: python3
    
        from slash.models import command
        
        @command(bot.slashclient, name="hi", description="Hello!")
        async def hi(ctx, user: discord.Member = None):
            user = user or ctx.user
            await ctx.reply(f"Hi {user.mention}")
    
    """
    def wrapper(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')
        result = SlashCommand(*args, **kwargs, callback=func)
        result.client.bot.loop.create_task(result.client.add_command(result))
        return result

    return wrapper
