import discord
import asyncio

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

MISSING = discord.utils.MISSING


def command(*args, cls=MISSING, **kwargs):
    """Same as :func:`~slash.models.command` but doesn't
    requires slashclient and is to be used in cogs only

    Parameters
    ------------
    name: :class:`~str`
        Name of the command, (required)
    description: Optional[:class:`~str`]
        Description of the command, (optional)
    options: Optional[List[:class:`~slash.models.Option`]]
        Options for the command, detects automatically if None given, (optional)
    cls: :class:`~slash.models.SlashCommand`
        The custom command class, must be a subclass of :class:`~slash.models.SlashCommand`, (optional)

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
        if isinstance(func, (CogSlashCommand, SlashCommand)):
            raise TypeError('Callback is already a slashcommand.')

        result = CogSlashCommand(*args, callback=func, cls=cls, **kwargs)
        return result

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
    
                if isinstance(value, CogSlashCommand):
                    slashcmds[elem] = value
        self.__slash_commands__ = tuple(cmd for cmd in slashcmds.values())
        return self

    def _inject(self, bot):
        new_list = []
        for i, cmd in enumerate(self.__slash_commands__):
            wrapped = _cmd(bot.slashclient, *cmd.args, cls=cmd._cls, **cmd.kwargs)
            cmd = wrapped(cmd.callback)
            cmd.cog = self.__class__
            new_list.append(cmd)
            setattr(self, cmd.name, cmd.callback)
            
        self.__slash_commands__ = tuple(c for c in new_list)
        return super()._inject(bot)
        
    def _eject(self, bot):
        slash, loop = bot.slashclient, bot.loop
        for cmd in self.__slash_commands__:
            loop.create_task(slash.remove_command(cmd.name))
            
        super()._eject(bot)
