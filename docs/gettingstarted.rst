Getting Started
================

Where do we start?
******************

Before we begin please read the `quickstart`_ page first
to know basics of this module

Making a slash command.
***********************

The basics
------------

Firstly we will know to make a simple command

.. code-block:: python3

    @slash.command(name="cmdname", description="my desc")
    async def some_command(ctx):
        await ctx.reply("My content here!")

Making a little bit complicated command.
----------------------------------------

.. code-block:: python3

    @slash.command(name="hello", description="says hello to you or other!")
    async def some_command(ctx, user: discord.Member = None):
        user = user or ctx.author
        await ctx.reply(f"Hello! {user.mention}")

Hiding a command response.
--------------------------

.. code-block:: python3

    @slash.command(name="secret", description="my desc")
    async def some_command(ctx):
        await ctx.reply("Shhhh! It's a secret", ephemeral=True)

Working with options.
*********************

The basics
-----------

Contents coming soon...
