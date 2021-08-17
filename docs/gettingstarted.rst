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
        await ctx.send("My content here!")
