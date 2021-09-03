# slash-commands
Since this is for personal use, it will not be published on pypi.

## Installation and Usage

To install this version, run 
```bash
pip install -U git+https://github.com/SilentJungle399/slash-commands@v1
```

### Usage

For a headstart, I'll provide an example here
If you want to view full documentation on it then [`click here`](https://dpy-slash.rtfd.io)

```py
from slash import *
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned_or('?'))
bot.slashclient = SlashClient(bot)

class Blep(SlashCommand):
    def __init__(self):
        super().__init__(
            bot.slashclient,
            name="blep",
            description = "Some blep description",
            callback = self.callback
        )

    async def callback(self, ctx: InteractionContext, pleb: str = None):
        await ctx.reply(f"why {pleb}", ephemeral=True)

# or

@command(bot.slashclient, name="test", description="test")
async def test(ctx):
    await ctx.reply("tested")

# or

@bot.slashclient.command(name="test2", description="test")
async def test(ctx):
    await ctx.reply(f"tested {ctx.author}")

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user} (ID: {bot.user.id})')
    await bot.slashclient.add_command(Blep())

bot.run("TOKEN")
```


### Screenshots

![image](https://user-images.githubusercontent.com/75272148/127775083-6722865b-b38a-4c1c-aeab-67792448224b.png)

![image](https://user-images.githubusercontent.com/75272148/127775088-8504cd9d-0b94-4e82-a683-e8acb6cc0f43.png)

![image](https://user-images.githubusercontent.com/75272148/127775094-75c435c7-6600-4a43-9433-80482692821f.png)
