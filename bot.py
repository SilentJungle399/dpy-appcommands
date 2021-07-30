
from discord.ext import commands
import discord
import os

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('?'), **kwargs)

    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')

    async def on_socket_response(self, data):
        print(data)


bot = Bot()

# write general commands here

bot.run("NzQwNTY4NzY2MTk4NDQ4MTkw.Xyq6aA.aEi-KSd_V9YL3UX9pg3hSDZFmoM")
