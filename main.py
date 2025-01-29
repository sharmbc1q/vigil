import logging
import asyncio
import warnings
from bot.bot import VigilBot
from config import settings

# Suppress the PyNaCl "voice not supported" warning.
warnings.filterwarnings("ignore", category=UserWarning, module="discord")

logging.basicConfig(level=logging.INFO)  # Set logging level
logger = logging.getLogger(__name__)    # Logger for main process


async def main():
    bot = VigilBot()

    try:
        async with bot:
            logger.info("Starting VigilBot...")
            await bot.start(settings.DISCORD_TOKEN)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Shutting down...")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")

    finally:
        logger.info("Initiating graceful shutdown...")
        if bot.cleanup_task and bot.cleanup_task.is_running():
            logger.info("Stopping cleanup task...")
            bot.cleanup_task.cancel()
            await bot.cleanup_task  # Wait for the task to stop
        await bot.close()
        logger.info("Bot has shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Properly run the top-level coroutine
    except RuntimeError as e:
        logger.error(f"Runtime error during event loop execution: {e}")