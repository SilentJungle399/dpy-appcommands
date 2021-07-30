from slash import SlashClient
from discord.ext import commands
from discord import http
import os
import json

class Bot(commands.Bot):
	def __init__(self, **kwargs):
		super().__init__(command_prefix=commands.when_mentioned_or('?'), **kwargs)
		self.slashclient = SlashClient(self)

	async def on_ready(self):
		print(f'Logged on as {self.user} (ID: {self.user.id})')

	async def on_socket_response(self, data):
		if data['t'] == "INTERACTION_CREATE":
			with open("ee.json", "w") as f1:
				json.dump(data, f1)

bot = Bot()

@bot.command()
async def aa(ctx):
	print(await bot.slashclient.get_commands())



bot.run(os.environ.get("TOKEN"))
