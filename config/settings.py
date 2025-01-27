import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    PREFIX = "!"
    HISTORY_FILE = "conversation_history.json"

settings = Settings()
