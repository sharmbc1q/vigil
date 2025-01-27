from bot.bot import VigilBot
from config import settings


if __name__ == "__main__":
    bot = VigilBot()
    bot.run(settings.DISCORD_TOKEN)
