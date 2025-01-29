import discord
from discord.ext import commands
from discord.ext import tasks
from config import settings
from bot.models.conversation import ConversationManager
import logging
from datetime import datetime, timedelta

class VigilBot(commands.Bot):
    def __init__(self):
        self.logger = logging.getLogger("Vigil.Bot")
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.typing = True  # Ensure typing indicator is supported
        self.convo_manager = ConversationManager()

        super().__init__(
            command_prefix=settings.PREFIX,
            intents=intents,
            help_command=None
        )

        # Schedule periodic tasks
        self.cleanup_task = self.start_cleanup_task()
        self.logger.info("\033[1;32mBot initialized successfully\033[0m")

    def start_cleanup_task(self):
        """Start and configure periodic cleanup task."""
        @tasks.loop(hours=24)  # Run every 24 hours
        async def cleanup_task():
            """Clean expired short-term memories."""
            try:
                self.logger.info("\033[1;34mStarting daily memory cleanup task...\033[0m")
                await self.convo_manager.clean_expired_short_term()
                self.logger.info("\033[1;32mDaily memory cleanup completed\033[0m")
            except Exception as e:
                self.logger.error(f"\033[1;31mError in cleanup task: {e}\033[0m")

        # Start the task and log the next run time
        cleanup_task.start()
        next_run = datetime.now() + timedelta(hours=24)
        self.logger.info(f"\033[1;33mNext cleanup scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
        
        return cleanup_task

    async def setup_hook(self):
        try:
            await self.load_extension("bot.cogs.message_handler")
            await self.load_extension("bot.cogs.image_commands")
            await self.tree.sync()
            print(f'{self.user} has connected to Discord!')
        except Exception as e:
            print(f"Error in setup_hook: {e}")

    async def on_ready(self):
        print(f'Bot is ready!')

    async def close(self):
        """Ensure cleanup on shutdown."""
        print("Shutting down VigilBot...")
        if self.cleanup_task.is_running():
            try:
                print("Stopping cleanup task...")
                self.cleanup_task.cancel()
                await self.cleanup_task
            except Exception as e:
                print(f"Error stopping cleanup task: {e}")
        await super().close()
        print("Cleanup task stopped. Bot is fully shut down.")