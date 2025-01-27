import anthropic
from config import settings

class AIService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
    
    async def should_search_web(self, question: str) -> bool:
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"Given this question: '{question}'\nDoes it need web search? Reply 'yes' or 'no'."
                }],
                temperature=0
            )
            return response.content[0].text.strip().lower() == 'yes'
        except Exception as e:
            print(f"Search decision error: {e}")
            return False

    async def generate_response(self, messages, system_prompt):
        return self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=messages,
            system=system_prompt,
            temperature=0.9
        )
