import httpx
from config import settings

class SearchService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

    async def search_web(self, query: str):
        data = {
            "model": "sonar",
            "messages": [{
                "role": "system",
                "content": "Provide accurate, concise information."
            }, {
                "role": "user",
                "content": f"{query}. Provide recent, accurate information."
            }],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        try:
            response = await self.client.post(
                "https://api.perplexity.ai/chat/completions",
                json=data,
                headers=self.headers
            )
            return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else None
        except Exception as e:
            print(f"Search error: {e}")
            return None
