import sys
import types
import discord
import importlib

from .utils import *
from .exceptions import *
from .types import StoredCommand
from .models import InteractionContext, SlashCommand, command as _cmd

from discord import http, ui
from discord.ext import commands
from discord.enums import InteractionType
from typing import List, Optional, Tuple, Union, Dict, Mapping


class Bot(commands.Bot):
    """The Bot
    This is fully same as :class:`~discord.ext.commands.Bot`

    Example
    ---------

    .. code-block:: python3

        import appcommands

        bot = appcommands.Bot(command_prefix="$")

    """
    def __init__(self, **options):
        """Constructor"""
        super().__init__(**options)
        self.appclient = self.get_app_client()

    def slash(self, *args, **kwargs) -> SlashCommand:
        """Adds a command to bot
        same as :func:`~appcommands.client.AppClient.command`

        Parameters
        -----------
        name: :class:`~str`
            name of the command, defaults to function name, (required)
        description: Optional[:class:`~str`]
            description of the command, required
        guild: Optional[:class:`~str`]
            id of the guild for which command is to be added, (optional)
        options: Optional[List[:class:`~appcommands.models.Option`]]
            the options for command, can be empty
        cls: :class:`~appcommands.models.SlashCommand`
            The custom command class, must be a subclass of :class:`~appcommands.models.SlashCommand`, (optional)

        Example
        ---------

        .. code-block:: python3

            @bot.slash(name="Hi", description="Hello!")
            async def some_func(ctx):
                await ctx.reply("Hello!")

        Raises
        --------
        TypeError
           The passed callback is not coroutine or it is already a SlashCommand

        Returns
        --------
        :class:`~appcommands.models.SlashCommand`
            The slash command.
        """
        return self.appclient.command(*args, **kwargs)

    def get_app_client(self):
        """The method usually implemented to use custom appclient"""
        return AppClient(self)

class AutoShardedBot(commands.AutoShardedBot):
    """The AutoShardedBot class
    This is fully same as :class:`~discord.ext.commands.AutoShardedBot`

    Example
    ---------

    .. code-block:: python3

        import appcommands

        bot = appcommands.AutoShardedBot(command_prefix="$")

    """
    def __init__(self, **options):
        """Constructor"""
        super().__init__(**options)
        self.appclient = self.get_app_client()

    def slash(self, *args, **kwargs) -> SlashCommand:
        """Adds a command to bot
        same as :func:`~appcommands.client.AppClient.command`

        Parameters
        -----------
        name: :class:`~str`
            name of the command, defaults to function name, (required)
        description: Optional[:class:`~str`]
            description of the command, required
        guild: Optional[:class:`~str`]
            id of the guild for which command is to be added, (optional)
        options: Optional[List[:class:`~appcommands.models.Option`]]
            the options for command, can be empty
        cls: :class:`~appcommands.models.SlashCommand`
            The custom command class, must be a subclass of :class:`~appcommands.models.SlashCommand`, (optional)

        Example
        ---------

        .. code-block:: python3

            @bot.slash(name="Hi", description="Hello!")
            async def some_func(ctx):
                await ctx.reply("Hello!")

        Raises
        --------
        TypeError
           The passed callback is not coroutine or it is already a SlashCommand

        Returns
        --------
        :class:`~appcommands.models.SlashCommand`
            The slash command.
        """
        return self.appclient.command(*args, **kwargs)

    def get_app_client(self):
        """The method usually implemented to use custom appclient"""
        return AppClient(self)

class AppClient:
    """Slash Client handler class for bot
    
    Parameters
    -----------
    bot: Union[:class:`~discord.ext.commands.Bot`, :class:`~discord.ext.commands.AutoShardedBot`]
        Your dpy bot
    logging: :class:`~bool`
        prints all the logs of this module, defaults to False
    
    Raises
    -------
    ValueError
        The bot has already a appclient registered with this module
    """
    def __init__(self,
                 bot: Union[commands.Bot, commands.AutoShardedBot],
                 logging: bool = False):
        self.bot: commands.Bot = bot
        if hasattr(bot, "appclient"):
            raise ValueError(
                "Bot has already a appclient registered with this module")
        self.bot.appclient = self
        self.logging: bool = logging
        self._views: Dict[str, Tuple[ui.View, ui.Item]] = {}
        self.__commands = {}
        self.bot.add_listener(self.socket_resp, "on_interaction")

    @property
    def commands(self) -> Mapping[int, StoredCommand]:
        """Returns all the command listeners added to the instance.

        Returns
        ---------
        Mapping[:class:`~int`, :class:`~appcommands.types.StoredCommand`]
          The json of commands."""
        return types.MappingProxyType(self.__commands)

    def command(self, *args, cls=MISSING, **kwargs) -> SlashCommand:
        """Adds a command to bot

        Parameters
        -----------
        name: :class:`~str`
            name of the command, defaults to function name, (required)
        description: Optional[:class:`~str`]
            description of the command, required
        options: Optional[List[:class:`~appcommands.models.Option`]]
            the options for command, can be empty
        cls: :class:`~appcommands.models.SlashCommand`
            The custom command class, must be a subclass of :class:`~appcommands.models.SlashCommand`, (optional)

        Example
        ---------

        .. code-block:: python3

            from slash import AppClient
            
            slash = AppClient(bot, logging=True)
            @bot.appclient.command(name="Hi", description="Hello!")
            async def some_func(ctx):
                await ctx.reply("Hello!")
                
            # and 
            
            @slash.command(name="Hello", description="Hello")
            async def hello(ctx):
                await ctx.reply("Hello")

        Raises
        --------
        TypeError
           The passed callback is not coroutine or it is already a SlashCommand

        Returns
        --------
        :class:`~appcommands.models.SlashCommand`
            The slash command.
        """
        def decorator(func):
            wrapped = _cmd(self, *args, cls=cls, **kwargs)
            resp = wrapped(func)
            return resp

        return decorator

    def log(self, message: str):
        """Logs the works
        
        Parameters
        -----------
        message: :class:`~str`
            The message which is to be logged"""
        if self.logging:
            print(message)

    def get_interaction_context(self):
        """The method usually implemented to use custom contexts"""
        return InteractionContext(self.bot, self)

    async def socket_resp(self, interaction):
        if interaction.type == InteractionType.application_command:
            if int(interaction.data['id']) in self.__commands:
                command = self.__commands[int(interaction.data['id'])]
                context = await (self.get_interaction_context()).from_interaction(interaction)

                cmd = (command['command'])
                if cmd.cog:
                    cog = self.bot.cogs.get(cmd.cog.qualified_name)
                    if cog:
                        return await (getattr(cog, cmd.callback.__name__))(**context.kwargs)
                await cmd.callback(**context.kwargs)

        elif interaction.type == InteractionType.component:
            interactctx = interaction
            custom_id = interactctx.data['custom_id']

            try:
                view, item = self._views[custom_id]
            except:
                return

            item.refresh_state(interactctx)
            view._dispatch_item(item, interactctx)

    async def fetch_commands(self, guild_id: Optional[int] = None) -> List[SlashCommand]:
        """fetch a list of slash command currently the bot has

        Parameters
        -------------
        guild_id: Optional[:class:`~int`]
            Should be given to fetch guild commands. (optional)
        """
        while not self.bot.is_ready():
            await self.bot.wait_until_ready()
        add = ""
        if guild_id:
            add = f"/guilds/{guild_id}"

        data = await self.bot.http.request(route=http.Route(
            "GET", f"/applications/{self.bot.user.id}{add}/commands"))
        ret = []
        for i in data:
            if i["type"] == 1:
                ret.append(SlashCommand.from_dict(self, i))

        return ret

    def get_commands(self) -> Dict[str, SlashCommand]:
        """Gets every command registered in the current running instance"""
        ret = {}

        for i in self.__commands:
            ret[self.__commands[i]['command'].name] = self.__commands[i]['command']

        return ret

    def get_command(self, name: str) -> SlashCommand:
        """Gives a command registered in this module
        
        Parameters
        -----------
        name: :class:`~str`
            the name from which command is to be found"""

        return (self.get_commands()).get(name)

    async def add_command(self, command: SlashCommand):
        """Adds a slash command to bot

        Parameters
        -----------
        command: :class:`~appcommands.models.SlashCommand`
            The command to be added
        
        Raises
        -------
        .CommandExists
            That slash cmd is already registered in bot with this module"""
        slashcmds = await self.fetch_commands(None)

        if command.guild:
            slashcmds = await self.fetch_commands(command.guild)

        if command.name in self.get_commands():
            raise CommandExists(
                f"Command '{command.name}' has already been registered!")
        else:
            if command in slashcmds:
                await self.remove_command(command.name)

            add = ""
            l_add = ""
            if command.guild:
                add = f"/guilds/{command.guild}"
                l_add = f"Guild command for '{command.guild}'"

            resp = await self.bot.http.request(route=http.Route(
                "POST", f"/applications/{self.bot.user.id}{add}/commands"),
                                        json=command.ret_dict())

            self.log(f"Slash command '{command.name}' (ID: {resp['id']}) registered! {l_add}")

            self.__commands[int(resp['id'])] = {
                "guild": None if 'guild_id' not in resp else int(resp['guild_id']),
                "command": command
            }

    def reload_command(self, command: SlashCommand):
        """Reloads a slash command

        Parameters
        -----------
        command: :class:`~appcommands.models.SlashCommand`
            The command which is to be reloaded

        Raises
        --------
        .CommandNotRegistered
            That command is not registered"""
        a = self.__commands
        listenerlist = {self.__commands[i]['command'].name: i for i in self.__commands}
        _id = listenerlist.get(command.name)

        if not _id:
            raise CommandNotRegistered(
                f"Command '{command.name}' has not been registered.")
        else:
            self.__commands.pop(_id)
            self.__commands[_id] = {
                "guild": command.guild,
                "command": command
            }

            self.log(f"Slash command '{command.name}' reloaded!")

    async def remove_command(self, name: str):
        """Removes command from the name given

        Parameters
        ------------
        name: :class:`~str`
            Name of the command"""
        listenerlist = {self.__commands[i]['command'].name: i for i in self.__commands}
        _id = listenerlist.get(name)

        if not _id:
            raise CommandDoesNotExists(f"Command '{name}' does not exist!")
        else:
            await self.bot.http.request(route=http.Route(
                "DELETE", f"/applications/{self.bot.user.id}/commands/{_id}"))

            self.__commands.pop(_id)

    def load_extension(self, name: str):
        """Load a command from an external file.

        Parameters
        -----------
        name: :class:`~str`
            Name of the file.
            eg: `client.load_extension('commands.ping')` loads command from `commands/ping.py`

        Raises
        -------
        .LoadFailed
            When extension could not be loaded or does not have a `setup()` method.
        """
        spec = importlib.util.find_spec(name)
        lib = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[name]
            raise LoadFailed(f"Extension '{name}' could not be loaded!")

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            raise LoadFailed(f"Extension '{name}' has no method 'setup'!")

        try:
            self.bot.loop.create_task(self.add_command(setup(self.bot)))
        except Exception as e:
            raise e

    def reload_extension(self, name: str):
        """Reload a command from an external file.

        Parameters
        -----------
        name: :class:`~str`
            Name of the file.
            eg: `client.reload_extension('commands.ping')` reloads command from `commands/ping.py`

        Raises
        -------
        .LoadFailed
            When extension could not be reloaded or does not have a `setup()` method.
        """
        spec = importlib.util.find_spec(name)
        lib = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[name]
            raise LoadFailed(f"Extension '{name}' could not be loaded!")

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            raise LoadFailed(f"Extension '{name}' has no method 'setup'!")

        try:
            self.reload_command(setup(self.bot))
        except Exception as e:
            raise e
