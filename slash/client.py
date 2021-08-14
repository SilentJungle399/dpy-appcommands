import importlib
from typing import Coroutine, List, Tuple
import discord
Item = discord.ui.Item
from .models import *
from .exceptions import *
from discord import http, ui
from discord.enums import InteractionType
from discord.ext import commands
from discord.interactions import Interaction
import sys

class SlashClient:

    def __init__(self, bot: commands.Bot, logging: bool = False) -> None:
        self.bot: commands.Bot = bot
        self.logging: bool = logging
        self._listeners = {}
        self._views: Dict[str, Tuple[ui.View, Item]] = {}
        self.bot.add_listener(self.socket_resp, "on_interaction")
        self.command = command

    def log(self, message):
        if self.logging:
            print(message)

    async def socket_resp(self, interaction):
        if interaction.type == InteractionType.application_command:
            if interaction.data['name'] in self._listeners:
                context = await InteractionContext(self.bot, self).from_interaction(interaction)
                await (self._listeners[context.data["name"]]).callback(context)

        elif interaction.type == InteractionType.component:
            interactctx = interaction
            custom_id = interactctx.data['custom_id']

            view, item = self._views[custom_id]

            item.refresh_state(interactctx)
            view._dispatch_item(item, interactctx)

    async def get_commands(self) -> List[SlashCommand]:
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

    async def add_command(self, command: SlashCommand):
        slashcmds = await self.get_commands()
        if command.name in self._listeners:
            raise CommandExists(f"Command '{command.name}' has already been registered!")
        else:
            self._listeners[command.name] = command
            self.log(f"Slash command '{command.name}' registered!")

            checks = list(map(lambda a: a.name, slashcmds))
            
            if command.name not in checks:
                await self.bot.http.request(
                    route = http.Route("POST", f"/applications/{self.bot.user.id}/commands"),
                    json = command.ret_dict()
                )

    def reload_command(self, command: SlashCommand):
        if command.name not in self._listeners:
            raise CommandNotRegistered(f"Command '{command.name}' has not been registered.")
        else:
            self._listeners.pop(command.name)
            self._listeners[command.name] = command
            self.log(f"Slash command '{command.name}' reloaded!")

    async def remove_command(self, name: str):
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