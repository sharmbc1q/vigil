import discord
from discord.ext import commands
from config import settings

class VigilBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=settings.PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        await self.load_extension("bot.cogs.message_handler")
        await self.load_extension("bot.cogs.image_commands")
        await self.tree.sync()

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
