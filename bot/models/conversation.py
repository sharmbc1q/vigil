import json
import os
from collections import defaultdict
from config import settings

class ConversationManager:
    def __init__(self):
        self.conversations = defaultdict(list)
        self.load_history()

    def add_message(self, user_id: int, user_message: str, bot_response: str):
        self.conversations[user_id].append({
            "user": user_message,
            "assistant": bot_response
        })
        self.save_history()

    def get_history(self, user_id: int) -> list:
        return [
            {"role": "user", "content": msg["user"]} if i % 2 == 0 
            else {"role": "assistant", "content": msg["assistant"]}
            for msg in self.conversations[user_id]
            for i in range(2)
        ]

    def save_history(self):
        try:
            history_dict = {str(k): v for k, v in self.conversations.items()}
            with open(settings.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def load_history(self):
        try:
            if os.path.exists(settings.HISTORY_FILE):
                with open(settings.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history_dict = json.load(f)
                    self.conversations = defaultdict(list, {
                        int(k): v for k, v in history_dict.items()
                    })
        except Exception as e:
            print(f"Error loading history: {e}")
