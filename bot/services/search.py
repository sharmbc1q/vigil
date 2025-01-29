import httpx
import re  # For filtering specific data like the price
from config import settings

class SearchService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

    async def search_web(self, query: str):
        """
        Perform a web search using Perplexity API with improved error handling.
        """
        data = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise search assistant. Provide only factual data and numbers. Focus on accuracy and recency."
                },
                {
                    "role": "user",
                    "content": f"What are the exact facts about: {query}"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 150
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    json=data,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    return "I couldn't find any current information about that."
                
                if response.status_code != 200:
                    print(f"Perplexity API error: {response.status_code} - {response.text}")
                    return None

                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Clean up the response
                content = content.replace('*', '').strip()
                if '[' in content:
                    content = content.split('[')[0].strip()

                return content

        except Exception as e:
            print(f"Search error: {e}")
            return None