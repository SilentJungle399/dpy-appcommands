from discord.ext.commands.flags import flag
from slash import *
from discord.ext import commands
from discord import http
import os
import json
from dotenv import load_dotenv

load_dotenv()

class Bot(commands.Bot):
	def __init__(self, **kwargs):
		super().__init__(command_prefix=commands.when_mentioned_or('?'), **kwargs)
		self.slashclient = SlashClient(self)

	async def on_ready(self):
		print(f'Logged on as {self.user} (ID: {self.user.id})')

	async def on_socket_response(self, data):
		if data['t'] == "INTERACTION_CREATE":
			with open("ee.json", "w") as f1:
				json.dump(data, f1, indent = 4)

	def register_command(self, command: SlashCommand):
		self.loop.create_task(self.slashclient.add_command(command))

bot = Bot()

@bot.command()
async def aa(ctx):
	print(await bot.slashclient.get_commands())

class test(SlashCommand):
	def __init__(self):
		super().__init__(
			bot.slashclient, 
			name="test", 
			description = "some description", 
			options = [
				{
					"type": 3,
					"name": "ee",
					"description": "some ee",
					"required": False
				}
			]
		)

	async def callback(self, ctx: InteractionContext):
		await ctx.reply("something", flags = MessageFlags.EPHEMERAL)

@bot.event
async def on_ready():
	print(f'Logged on as {bot.user} (ID: {bot.user.id})')
	await bot.slashclient.add_command(test())

bot.run(os.environ.get("TOKEN"))
