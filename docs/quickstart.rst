Quickstart
==========

Before doing anything, it is highly recommended to read discord.py's quickstart.
You can find it by clicking :ref:`this here <discord:quickstart>`.

Firstly, we will begin from installing dpy-appcommands:

Installing
-----------

.. code-block::

    pip install -U git+https://github.com/SilentJungle399/dpy-appcommands

Then we will make a client for it

Initialising
-------------

.. code-block:: python3

    from discord.ext import commands
    from appcommands import Bot

    bot = Bot(command_prefix="$")

Then we will make a command

Creating a command
-------------------

.. code-block:: python3

    @bot.slash(name="hi", description="Hello!")
    async def hi(ctx):
        await ctx.reply("Hello")

