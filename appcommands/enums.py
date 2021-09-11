import typing
import discord

from enum import IntEnum


class OptionType(IntEnum):
    """
    Equivalent of `ApplicationCommandOptionType <https://discord.com/developers/docs/interactions/slash-commands#applicationcommandoptiontype>`_  in the Discord API.
    """

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    FLOAT = 10

    @classmethod
    def from_type(cls, t: type):
        """Get a specific OptionType from a type (or object).

        Parameters
        -----------
        t: :class:`~type`
            The type or object to get a OptionType for.

        Returns
        ---------
        :class:`~appcommands.enums.OptionType`
            OptionType if found
        :class:`~None`
            None if not found
        """

        if issubclass(t, str):
            return cls.STRING
        if issubclass(t, bool):
            return cls.BOOLEAN
        # The check for bool MUST be above the check for integers as booleans subclass integers
        if issubclass(t, int):
            return cls.INTEGER
        if issubclass(t, discord.User) or issubclass(t, discord.Member):
            return cls.USER
        if issubclass(t, discord.abc.GuildChannel):
            return cls.CHANNEL
        if issubclass(t, discord.Role):
            return cls.ROLE
        if hasattr(typing, "_GenericAlias"):  # 3.7 onwards
            # Easier than imports
            if hasattr(t, "__origin__"):
                if t.__origin__ is typing.Union:
                    # proven in 3.7.8+, 3.8.6+, 3.9+ definitively
                    return cls.MENTIONABLE
        if not hasattr(typing, "_GenericAlias"):  # py 3.6
            if isinstance(t, typing._Union):  # noqa
                return cls.MENTIONABLE

        if issubclass(t, discord.Object):
            return cls.MENTIONABLE

        if issubclass(t, float):
            return cls.FLOAT


class MessageFlags:
    EPHEMERAL = 1 << 6
