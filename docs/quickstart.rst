Quickstart
==========

Before doing anything, it is highly recommended to read discord.py's quickstart.
You can find it by clicking :ref:`this here <discord:quickstart>`.

Firstly, we will begin from installing slash:

Installing
-----------

.. code-block::

    pip install -U git+https://github.com/SilentJungle399/slash-commands

Then we will make a client for it

Initialising
-------------

.. code-block:: python3

    from discord.ext import commands
    from slash import AppClient

    bot = commands.Bot(command_prefix="$")
    slash = AppClient(bot)

Then we will make a command

Creating a command
-------------------

.. code-block:: python3

    @slash.command(name="hi", description="Hello!")
    async def hi(ctx):
        await ctx.reply("Hello")

