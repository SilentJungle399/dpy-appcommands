Getting Started
================


Where do we start?
******************

Before we begin please read the `quickstart <https://dpy-slash.readthedocs.io/en/latest/quickstart.html>`_ page first
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

Making a little bit complicated command
----------------------------------------

.. code-block:: python3

    @slash.command(name="hello", description="says hello to you or other!")
    async def some_command(ctx, user: discord.Member = None):
        user = user or ctx.author
        await ctx.reply(f"Hello! {user.mention}")

Sending a hidden message
--------------------------

.. code-block:: python3

    @slash.command(name="secret", description="my desc")
    async def some_command(ctx):
        await ctx.reply("Shhhh! It's a secret", ephemeral=True)

Working with options.
*********************

The basics
-----------

Options are currently available in 2 forms

+-------+--------------------------------+
| Sr.no |  Place                         |
+=======+================================+
|  1.   |  As a parameter in callback    |
+-------+--------------------------------+
|  2.   |  In ``@slash.command()``       |
+-------+--------------------------------+

Options are a basic thing for commands,
when it is used in parameters and type of parameter is not defined,
then it takes the value as ``string``,
and when value is not defined then it makes option ``required``

When Option is added in both forms then it takes ``@slash.command()`` one,
not ``async def hi(ctx, text: str):``


Let's start with 1st one

Required options
------------------

This will add ``required`` option

.. code-block:: python3

    @slash.command(name="say", description="Repeats your text")
    async def say(ctx, text: str):
        await ctx.reply(text)


Optional options.
-----------------

This will add optional options

.. code-block:: python3

    @slash.command(name="say", description="Repeats your text")
    async def say(ctx, text: str = "Please enter a text!"):
        await ctx.reply(text)

Here, text is defined in parameter, so it is optional while in above one it is not defined
so it was optional

2nd one

Custom Options
----------------

.. code-block:: python3

    from slash import Option, OptionType

    @slash.command(name="number", description="Your favourite number", options=[Option(name="number", description="your favourite number", type=OptionType.NUMBER, required=True)])
    async def say(ctx, number):
        await ctx.reply('your favourite number is ' + str(number))



Working with choices
********************

The basics
----------

Choices are a useful thing for options

For ex - you want to make commands like that user will be able to type some
texts which you want.
In this case choices are used

Let's make a slashcommand with choices

Making a slashcommand with choices
-----------------------------------

.. code-block:: python3
    
    from slash import Option, Choice

    choices = [Choice(name="dog"),Choice(name="cat"),Choice(name="tiger")]
    opts = [Option(name="animal", description="Choose an animal", choices=choices)]

    @slash.command(name="animal", description="choose an animal", options=opts)
    async def Animal(ctx, animal: str):
       await ctx.reply(f"You chose {animal}")
