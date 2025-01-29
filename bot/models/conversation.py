import asyncio
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from bot.models.database import ShortTermMemory, LongTermMemory, initialize_database, SessionLocal
from bot.services.ai import AIService
import discord
from sqlalchemy import or_
import pytz


class ConversationManager:
    SHORT_TERM_MEMORY_DURATION = timedelta(hours=24)  # 24-hour expiration
    ai_service = AIService()

    def __init__(self):
        # Ensure the database tables exist
        initialize_database()

    @asynccontextmanager
    async def get_db(self):
        """Provide a database session for async operations."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Short-Term Memory Management
    async def add_to_short_term(self, user_id: int, user_message: str, bot_response: str):
        """Add a memory to short-term storage with an expiration time."""
        async with self.get_db() as db:
            current_time = datetime.now(pytz.UTC)
            expiration_time = current_time + self.SHORT_TERM_MEMORY_DURATION
            short_memory = ShortTermMemory(
                user_id=user_id,
                user_message=user_message,
                bot_response=bot_response,
                expiration_time=expiration_time
            )
            db.add(short_memory)
            db.commit()

    async def get_short_term(self, user_id: int):
        """Retrieve active short-term memories with conversation pairing"""
        async with self.get_db() as db:
            current_time = datetime.now(pytz.UTC)
            memories = (
                db.query(ShortTermMemory)
                .filter(ShortTermMemory.user_id == user_id)
                .filter(ShortTermMemory.expiration_time > current_time)
                .order_by(ShortTermMemory.creation_time.desc())
                .limit(6)  # Get last 3 pairs of interactions
                .all()
            )
            # Pair messages with their responses
            paired_memories = []
            for i in range(0, len(memories)-1, 2):
                if i+1 < len(memories):
                    paired_memories.append({
                        "user": memories[i+1].user_message,
                        "assistant": memories[i].bot_response
                    })
            return paired_memories[::-1]  # Return in chronological order

    async def clean_expired_short_term(self):
        """Remove expired short-term memories"""
        async with self.get_db() as db:
            try:
                current_time = datetime.now(pytz.UTC)
                
                # Get expired memories based on their expiration time
                old_memories = db.query(ShortTermMemory).filter(
                    ShortTermMemory.expiration_time < current_time
                ).all()
                
                deleted_count = 0
                for memory in old_memories:
                    # Verify the memory is truly expired
                    if memory.expiration_time < current_time:
                        db.delete(memory)
                        deleted_count += 1
                
                db.commit()
                print(f"Cleaned up {deleted_count} expired memories")
                
            except Exception as e:
                print(f"Error during memory cleanup: {e}")
                db.rollback()

    # Long-Term Memory Management
    async def extract_server_user_id(self, user_id: int, message: discord.Message):
        """Extracts server id and user id from message."""
        server_id = message.guild.id if message.guild else None
        return user_id, server_id

    async def save_to_long_term(self, user_id: int, content: str, message: discord.Message):
        """Classify and save memory to long-term storage."""
        user_id, server_id = await self.extract_server_user_id(user_id, message)
        async with self.get_db() as db:
            classification = await self.ai_service.classify_memory(content)  # Invoke AI classification API
            type_ = classification["type"]  # e.g., "preference", "fact"
            importance = classification["importance"]  # Importance rating (1-5)

            # Additional logic: Assign 'preference' type for specific keywords like 'favorite'
            if "favorite" in content.lower():
                type_ = "preference"
                importance = max(importance, 4)

            long_memory = LongTermMemory(
                user_id=user_id,
                server_id=server_id,
                type=type_,
                content=content,
                importance=importance
            )
            db.add(long_memory)
            db.commit()

    async def get_long_term(self, user_id: int, message: discord.Message):
        """Retrieve all long-term memories for a user, filter by server ID if available."""
        user_id, server_id = await self.extract_server_user_id(user_id, message)
        async with self.get_db() as db:
            query = db.query(LongTermMemory).filter(LongTermMemory.user_id == user_id)
            if server_id:
                # Use OR condition to get both server-specific and non-server memories
                query = query.filter(or_(
                    LongTermMemory.server_id == server_id,
                    LongTermMemory.server_id.is_(None)
                ))
            return query.all()

    async def delete_long_term(self, user_id: int, memory_type: str = None):
        """Delete specific or all long-term memories for a user."""
        async with self.get_db() as db:
            query = db.query(LongTermMemory).filter(LongTermMemory.user_id == user_id)
            if memory_type:
                query = query.filter(LongTermMemory.type == memory_type)
            query.delete()
            db.commit()

    # Combine Short-Term and Long-Term Memory for Context
    async def get_user_memory(self, user_id: int, message: discord.Message, query: str = None):
        """
        Retrieve both short-term and relevant long-term memory for a user.
        Implements AI-based memory recall system.
        """
        # Get recent conversation context (short-term)
        short_term_memories = await self.get_short_term(user_id)
        
        # Only keep last 3 interactions for immediate context
        short_term_memories = short_term_memories[-3:] if short_term_memories else []
        
        if not query:
            return {"short_term": short_term_memories, "long_term": []}
        
        # Use AI to determine if we need to recall memories
        if await self.ai_service.needs_memory_recall(query):
            long_term_memories = await self.get_long_term(user_id, message)
            
            # Score memories based on relevance to query
            scored_memories = []
            for memory in long_term_memories:
                # Skip bot-generated interpretations
                if "you said" in memory.content.lower() or "you mentioned" in memory.content.lower():
                    continue
                
                # Combined validation and scoring
                try:
                    # Single API call for both validation and scoring
                    score = await self.ai_service.get_memory_relevance_score(query, memory.content)
                    if score < 0.5:  # Lower threshold for better recall
                        continue
                    
                    # Apply importance boost
                    score *= memory.importance
                    scored_memories.append((score, memory.content))
                except Exception as e:
                    self.logger.error(f"Memory scoring error: {e}")
                    continue
            
            # Sort by score and take top 2 most relevant memories
            filtered_long_term = [
                content for _, content in sorted(scored_memories, reverse=True)
            ][:2]

            # Filter based on relevance to current conversation
            relevant_long_term = []
            for memory in filtered_long_term:
                if await self.ai_service.check_memory_relevance(memory, query):
                    relevant_long_term.append(memory)

            # Format memories for better context if we found any
            if relevant_long_term:
                formatted_context = await self.ai_service.format_memories_for_response(relevant_long_term, query)
                if formatted_context:
                    relevant_long_term = [formatted_context]
        else:
            relevant_long_term = []

        return {
            "short_term": short_term_memories,
            "long_term": relevant_long_term
        }