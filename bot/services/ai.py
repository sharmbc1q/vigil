import anthropic
from config import settings
import json
import logging
import asyncio
from anthropic import APIError
from requests.exceptions import Timeout


class AIService:
    """
    Service for interacting with Anthropics Claude API for generating responses.
    """
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.logger = logging.getLogger("Vigil.AI")
    
    async def should_search_web(self, question: str) -> bool:
        """
        Determine whether a query requires a web search.
        """
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Would this question be better answered with a Google search or real-time data? Reply ONLY 'yes' or 'no'.
                    Answer 'yes' if the question:
                    - Needs current/accurate data (prices, weather, news)
                    - Asks about scientific facts or statistics
                    - Requires specific numerical data
                    - Could be answered by searching Google
                    - Involves current events or changing information
                    
                    Question: '{question}'"""
                }],
                temperature=0
            )
            answer = response.content[0].text.strip().lower()
            print(f"Web search classification for '{question}': {answer}")
            return answer == "yes"
        except Exception as e:
            print(f"Error checking if web search is required: {e}")
            return False

    async def should_save_to_long_term(self, content: str) -> bool:
        """
        Classify whether user input should be stored in long-term memory.
        """
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"Does this message contain a personal fact or preference about the user (e.g., favorites, important info)? Reply 'yes' or 'no'. Message: '{content}'"
                }],
                temperature=0
            )
            answer = response.content[0].text.strip().lower()
            print(f"Long-term memory classification for '{content}': {answer}")
            return answer == "yes"
        except Exception as e:
            print(f"Error checking long-term memory classification: {e}")
            return False

    async def extract_value(self, prompt: str) -> str:
        """Extract specific numerical data from text."""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Faster model for extraction
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Extraction error: {e}")
            return None

    async def generate_response(self, messages, personality_prompt: str):
        """
        Generate a conversational response with Vigil's personality.
        """
        try:
            # Filter out any system messages from the input
            filtered_messages = [msg for msg in messages if msg["role"] != "system"]
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=filtered_messages,
                system=personality_prompt,  # This is the correct way to set system message
                temperature=0.7
            )
            
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Error in AI response generation: {e}")
            return "*I couldn't process that, try again later!*"

    async def classify_memory(self, content: str) -> dict:
        """Classify memory type and importance with error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": f"Classify this memory. Format: JSON with 'type' (preference/fact) and 'importance' (1-5): '{content}'"
                    }],
                    temperature=0,
                    timeout=10.0  # Add timeout
                )
                # Rest of method remains same
                # Add retry on empty response
                if not response.content:
                    raise ValueError("Empty response")
                # Extract classification from response
                result = response.content[0].text.strip()
                try:
                    # Clean up the response to ensure it's valid JSON
                    result = result.replace("```json", "").replace("```", "").strip()
                    classification = json.loads(result)
                    return {
                        "type": classification.get("type", "fact"),
                        "importance": min(max(classification.get("importance", 1), 1), 5)
                    }
                except json.JSONDecodeError:
                    return {"type": "fact", "importance": 1}
            except (APIError, Timeout) as e:
                if attempt == max_retries - 1:
                    return {"type": "fact", "importance": 1}
                await asyncio.sleep(1.5 ** attempt)

    async def check_memory_relevance(self, memory: str, current_context: str) -> bool:
        """
        Check if a memory is relevant to the current conversation context.
        """
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Determine if this memory is relevant to the current context. Reply ONLY 'yes' or 'no'.
                    Memory: {memory}
                    Current context: {current_context}
                    
                    Guidelines:
                    - Say 'yes' if the memory provides context for the current topic
                    - Allow indirect relationships ("favorite" vs "preferred")
                    - Consider synonyms and related concepts
                    - Say 'yes' for any personal preference reference
                    """
                }],
                temperature=0
            )
            answer = response.content[0].text.strip().lower()
            self.logger.debug(f"Memory relevance check - Memory: '{memory}', Context: '{current_context}', Result: {answer}")
            return answer == "yes"
        except Exception as e:
            self.logger.error(f"Error checking memory relevance: {e}")
            return False



    async def format_memories_for_response(self, memories: list, query: str) -> str:
        """Format memories into a context string for response generation."""
        try:
            memories_text = "\n".join([f"- {m}" for m in memories])
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": f"""Given these memories about a user and their question, create a brief context summary:

                    Memories:
                    {memories_text}

                    Question: {query}

                    Format the summary to be natural and conversational, focusing only on relevant details.
                    """
                }],
                temperature=0.7
            )
            return response.content[0].text.strip()
        except Exception as e:
            self.logger.error(f"Error formatting memories: {e}")
            return ""


    async def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """Get semantic similarity score between two texts (0-1)"""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Rate similarity between these texts (0-1). Reply ONLY number.
                    
                    Text 1: {text1}
                    Text 2: {text2}
                    
                    Consider:
                    - Conceptual similarity
                    - Intent matching
                    - Entity relationships
                    - Implied meaning"""
                }],
                temperature=0
            )
            return float(response.content[0].text.strip())
        except:
            return 0

    async def validate_memory_match(self, query: str, memory: str) -> float:
        """Strict validation of memory matches to prevent hallucinations"""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Verify if this memory DIRECTLY contains user-stated information about: {query}
                    Memory: {memory}
                    Reply ONLY 'yes' or 'no'"""
                }],
                temperature=0
            )
            return 1.0 if response.content[0].text.strip().lower() == "yes" else 0.0
        except:
            return 0.0

    async def get_memory_relevance_score(self, query: str, memory: str) -> float:
        """Get combined relevance score (0-1) with single API call"""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this memory in relation to the query. Reply with JSON: 
                    {{
                        "score": 0-1, 
                        "reason": "direct match/related concept/not relevant"
                    }}
                    
                    Memory: {memory}
                    Query: {query}
                    
                    Scoring rules:
                    - 1.0 if memory contains direct user statement matching query
                    - 0.8 if memory contains related personal fact
                    - 0.5 if indirect connection
                    - 0.0 if irrelevant"""
                }],
                temperature=0
            )
            result = json.loads(response.content[0].text)
            return min(max(float(result.get("score", 1.0)), 0), 1)
        except Exception as e:
            self.logger.error(f"Scoring error: {e}")
            return 0

    async def needs_memory_recall(self, query: str) -> bool:
        """Determine if the query requires memory recall."""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"""Should I recall memories to answer this? Reply ONLY 'yes' or 'no':
                    {query}
                    
                    Guidelines:
                    - 'yes' for personal facts/preferences
                    - 'no' for general questions"""
                }],
                temperature=0
            )
            return response.content[0].text.strip().lower() == "yes"
        except Exception as e:
            self.logger.error(f"Recall check error: {e}")
            return False