import discord
import asyncio

from .utils import *
from .models import SlashCommand, Option, command as _cmd

from discord.ext.commands import Cog
from typing import Optional, Union, List

__all__ = ("command", "SlashCog")

class CogSlashCommand(object):
    def __init__(self, *args, cls, callback, **kwargs):
        self.args = args
        self.callback = callback
        self._cls = cls
        self.kwargs = kwargs
        
    def to_dict(self):
      return {}


def command(*args, cls=MISSING, **kwargs):
    """Same as :func:`~appcommands.models.command` but doesn't
    requires appclient and is to be used in cogs only

    Parameters
    ------------
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
    
        from slash import cog
        
        class MyCog(cog.SlashCog):
            @cog.command(name="hi", description="Hello!")
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
        if hasattr(func, "__slash__") and isinstance(func.__slash__, (CogSlashCommand, SlashCommand)):
            raise TypeError('Callback is already a slashcommand.')

        result = CogSlashCommand(*args, callback=func, cls=cls, **kwargs)
        func.__slash__ = result
        return func

    return wrapper


class SlashCog(Cog):
    """The cog for extensions

    Example
    ----------

    .. code-block:: python3

        from slash import cog

        class MyCog(cog.SlashCog):
            def __init__(self, bot):
                self.bot = bot

            @cog.command(name="test")
            async def test(self, ctx):
                await ctx.reply("tested!")

        def setup(bot):
            bot.add_cog(MyCog(bot))

    """
    __slash_commands__: tuple
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        slashcmds = {}
        for base in reversed(self.__class__.__mro__):
            for elem, value in base.__dict__.items():
                if elem in slashcmds:
                    del slashcmds[elem]
    
                if hasattr(value, "__slash__") and isinstance(value.__slash__, CogSlashCommand):
                    slashcmds[elem] = value
        self.__slash_commands__ = tuple(cmd for cmd in slashcmds.values())
        return self

    def _inject(self, bot):
        new_list = []
        for i, func in enumerate(self.__slash_commands__):
            cmd = func.__slash__
            new_cmd = cmd._cls(bot.appclient, *cmd.args, callback=cmd.callback, **cmd.kwargs)
            new_cmd.cog = self
            func.__slash__ = new_cmd
            bot.loop.create_task(bot.appclient.add_command(func.__slash__))
            new_list.append(new_cmd)
            setattr(self.__class__, new_cmd.callback.__name__, func)

        self.__slash_commands__ = tuple(c for c in new_list)
        return super()._inject(bot)
        
    def _eject(self, bot):
        slash, loop = bot.appclient, bot.loop
        for cmd in self.__slash_commands__:
            loop.create_task(slash.remove_command(cmd.name))
            
        super()._eject(bot)
