import importlib
from typing import Coroutine, List, Tuple, Union
import discord
Item = discord.ui.Item
from .models import InteractionContext, SlashCommand, command as _cmd
from .exceptions import *
from discord import http, ui
from discord.enums import InteractionType
from discord.ext import commands
from discord.interactions import Interaction
import sys

class SlashClient:
    """Slash Client handler class for bot
    
    Parameters
    -----------
    bot: Union[:class:`~discord.ext.commands.Bot`, :class:`~discord.ext.commands.AutoShardedBot`]
        Your dpy bot
    logging: bool
        prints all the logs of this module, defaults to False
    
    Raises
    -------
    ValueError
        The bot has already a slashclient registered with this module
    """
    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], logging: bool = False) -> None:
        self.bot: commands.Bot = bot
        if hasattr(bot, "slashclient"):
            raise ValueError("Bot has already a slashclient registered with this module")
        self.bot.slashclient = self
        self.logging: bool = logging
        self._listeners = {}
        self._views: Dict[str, Tuple[ui.View, Item]] = {}
        self.bot.add_listener(self.socket_resp, "on_interaction")

    def command(self, *args, **kwargs):
        """Adds a command to bot

        Parameters
        -----------
        name: str
            name of the command, defaults to function name
        description: str
            description of the command, required
        options: List[Dict]
            the options for command, can be empty

        Example
        ---------

        .. code-block:: python3

            @bot.slashclient.command(name="Hi", description="Hello!")
            async def some_func(ctx):
                await ctx.reply("Hello!")

        """
        def decorator(func):
            wrapped = _cmd(self, *args, **kwargs)
            wrapped(func)
            return func
        return decorator

    def log(self, message: str):
        """Logs the works
        
        Parameters
        -----------
        message: str
            The message which is to be logged"""
        if self.logging:
            print(message)

    async def socket_resp(self, interaction):
        if interaction.type == InteractionType.application_command:
            if interaction.data['name'] in self._listeners:
                context = await InteractionContext(self.bot, self).from_interaction(interaction)
                await (self._listeners[context.data["name"]]).callback(context,**context.kwargs)

        elif interaction.type == InteractionType.component:
            interactctx = interaction
            custom_id = interactctx.data['custom_id']

            view, item = self._views[custom_id]

            item.refresh_state(interactctx)
            view._dispatch_item(item, interactctx)

    async def get_commands(self) -> List[SlashCommand]:
        """Gives a list of slash command currently the bot have"""
        while not self.bot.is_ready():
            await self.bot.wait_until_ready()
        data = await self.bot.http.request(
            route = http.Route(
                "GET",
                f"/applications/{self.bot.user.id}/commands"
            )
        )
        ret = []
        for i in data:
            if i["type"] == 1:
                ret.append(SlashCommand.from_dict(self, i))

        return ret

    def get_command(self, name: str):
        """Gives a command registered in this module
        name: str
            the name from which command is to be found"""
        return self._listeners.get(name)

    async def add_command(self, command: SlashCommand):
        """Adds a slash command to bot

        Parameters
        -----------
        command: :class:`~slash.SlashCommand`
            The command to be added
        
        Raises
        -------
        .CommandExists
            That slash cmd is already in bot"""
        slashcmds = await self.get_commands()
        if command.name in self._listeners:
            raise CommandExists(f"Command '{command.name}' has already been registered!")
        else:
            checks = list(map(lambda a: a.name, slashcmds))
            if command in slashcmds:
                await self.remove_command(command.name)
            if command.name not in checks:
                await self.bot.http.request(
                    route = http.Route("POST", f"/applications/{self.bot.user.id}/commands"),
                    json = command.ret_dict()
                )
            self._listeners[command.name] = command
            self.log(f"Slash command '{command.name}' registered!")


    def reload_command(self, command: SlashCommand):
        """Reloads a slash command

        Parameters
        -----------
        command: :class:`~slash.SlashCommand`
            The command which is to be reloaded

        Raises
        --------
        .CommandNotRegistered
            That command is not registered"""
        if command.name not in self._listeners:
            raise CommandNotRegistered(f"Command '{command.name}' has not been registered.")
        else:
            self._listeners.pop(command.name)
            self._listeners[command.name] = command
            self.log(f"Slash command '{command.name}' reloaded!")

    async def remove_command(self, name: str):
        """Removes command from the name given
       
        Parameters
        ------------
        name: str
            Name of the command"""
        slashcmds = await self.get_commands()
        checks = list(map(lambda a: a.name, slashcmds))
        if name not in checks:
            raise CommandDoesNotExists(f"Command '{name}' does not exist!")
        else:
            id = slashcmds[checks.index(name)].id

            await self.bot.http.request(
                route = http.Route("DELETE", f"/applications/{self.bot.user.id}/commands/{id}")
            )

    def load_extension(self, name: str):
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
            print(e)

    def reload_extension(self, name: str):
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
            print(e)
