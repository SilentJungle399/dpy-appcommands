import importlib
from typing import List, Optional, Tuple, Union, Dict
import discord

Item = discord.ui.Item
from .models import InteractionContext, SlashCommand, command as _cmd
from .exceptions import *
from discord import http, ui
from discord.enums import InteractionType
from discord.ext import commands
import sys

class Bot(commands.Bot):
    # Remove comments and add docs

    # - inherits commands.Bot
    # - one extra attribute, slashclient, now inbuilt instead of being init by user previously
    def __init__(self, command_prefix, help_command = None, description = None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)

        self.slashclient = SlashClient(self, logging = True if options.get("slashlog") else False)

    # just a shorthand
    def slash(self, *args, **kwargs):
        self.slashclient.command(*args, **kwargs)

class SlashClient:
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
        The bot has already a slashclient registered with this module
    """
    def __init__(self,
                 bot: Union[commands.Bot, commands.AutoShardedBot],
                 logging: bool = False):
        self.bot: commands.Bot = bot
        if hasattr(bot, "slashclient"):
            raise ValueError(
                "Bot has already a slashclient registered with this module")
        self.bot.slashclient = self
        self.logging: bool = logging
        self._views: Dict[str, Tuple[ui.View, Item]] = {}
        self.__commands = {}
        self.bot.add_listener(self.socket_resp, "on_interaction")

    @property
    def commands(self) -> Dict[int, Dict]:
        """Returns all the command listeners added to the instance."""
        return self.__commands

    def command(self, *args, **kwargs):
        """Adds a command to bot

        Parameters
        -----------
        name: :class:`~str`
            name of the command, defaults to function name, (required)
        description: Optional[:class:`~str`]
            description of the command, required
        options: Optional[List[:class:`~slash.models.Option`]]
            the options for command, can be empty
        cls: :class:`~slash.models.SlashCommand`
            The custom command class, must be a subclass of :class:`~slash.models.SlashCommand`, (optional)

        Example
        ---------

        .. code-block:: python3

            from slash import SlashClient
            
            slash = SlashClient(bot, logging=True)
            @bot.slashclient.command(name="Hi", description="Hello!")
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

        """
        def decorator(func):
            wrapped = _cmd(self, *args, **kwargs)
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

    async def socket_resp(self, interaction):
        if interaction.type == InteractionType.application_command:
            if int(interaction.data['id']) in self.__commands:
                command = self.__commands[int(interaction.data['id'])]
                context = await InteractionContext(
                    self.bot, self).from_interaction(interaction)

                await (command['command']).callback(
                    context, **context.kwargs)

        elif interaction.type == InteractionType.component:
            interactctx = interaction
            custom_id = interactctx.data['custom_id']

            view, item = self._views[custom_id]

            item.refresh_state(interactctx)
            view._dispatch_item(item, interactctx)

    async def fetch_commands(self, guild_id: Optional[int]) -> List[SlashCommand]:
        """fetch a list of slash command currently the bot have"""
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

    def get_commands(self) -> dict[str, SlashCommand]:
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
        command: :class:`~slash.models.SlashCommand`
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
        command: :class:`~slash.models.SlashCommand`
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
                "DELETE", f"/applications/{self.bot.user.id}/commands/{id}"))

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
