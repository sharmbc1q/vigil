import discord
from discord.ext import commands
from bot.models.conversation import ConversationManager
from bot.services.ai import AIService
from bot.services.search import SearchService
from config.constants import SystemMessages
import pytz
from datetime import datetime


class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.convo_manager = ConversationManager()  # Handles short-term and long-term memory
        self.ai_service = AIService()  # Connects to Anthropics Claude API for generating messages
        self.search_service = SearchService()  # Connects to Perplexity API for web searches

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Process user messages and generate a response using AI, web search, or memory.
        """
        # Ignore messages from bots, including itself
        if message.author.bot:
            return

        # Check if the bot is directly mentioned
        if self.bot.user.mentioned_in(message):
            # Clean the question by removing the bot mention
            question = message.clean_content.replace(f'@{self.bot.user.display_name}', '').strip()

            # Skip if the user didn't provide a query
            if not question:
                return

            try:
                # Show typing indicator while the bot is processing the message
                async with message.channel.typing():
                    vigil_personality = SystemMessages.VIGIL_PERSONALITY
                    
                    if await self.ai_service.should_search_web(question):
                        search_result = await self.search_service.search_web(question)
                        if not search_result:
                            await message.channel.send(
                                "*Sorry! I'm having trouble fetching data right now. Try again later.*"
                            )
                            return

                        # If a web search was required, format the query with the search results
                        messages = [{
                            "role": "user",
                            "content": (
                                f"Here is factual data to answer with: {search_result}\n\n"
                                f"Now answer this question in your style: {question}\n\n"
                                "Remember to incorporate the factual data while maintaining your personality, "
                                "but don't say 'according to the search' or similar phrases."
                            )
                        }]
                    else:
                        # Retrieve user memory and combine it with the query for context
                        user_memory = await self.convo_manager.get_user_memory(
                            message.author.id,
                            query=question,
                            message=message
                        )
                        long_term_context = [
                            {"role": "assistant", "content": memory}
                            for memory in user_memory.get("long_term", [])
                        ]
                        short_term_context = [
                            {"role": "user", "content": mem["user"]}
                            if i % 2 == 0
                            else {"role": "assistant", "content": mem["assistant"]}
                            for i, mem in enumerate(user_memory.get("short_term", []))
                        ]

                        # Format short-term as alternating user/assistant messages
                        conversation_history = []
                        for exchange in user_memory.get("short_term", []):
                            conversation_history.append({"role": "user", "content": exchange["user"]})
                            conversation_history.append({"role": "assistant", "content": exchange["assistant"]})

                        # Keep last 2 user messages and their responses
                        recent_history = conversation_history[-4:] if len(conversation_history) >=4 else conversation_history

                        # Add long-term memories as background knowledge
                        memory_context = "Relevant memories:\n" + "\n".join(
                            [f"- {m}" for m in user_memory.get("long_term", [])]
                        ) if user_memory.get("long_term") else ""

                        # Prepare final message payload
                        messages = [
                            {"role": "system", "content": f"{vigil_personality}\n{memory_context}"},
                            *recent_history,
                            {"role": "user", "content": question}
                        ]

                    # Generate a response using the AI
                    response = await self.ai_service.generate_response(
                        messages=messages,
                        personality_prompt=vigil_personality
                    )
                    bot_response = response.strip()

                    # Save the interaction to short-term memory
                    await self.convo_manager.add_to_short_term(
                        message.author.id,
                        question,
                        bot_response
                    )

                    # Check if the interaction should be saved to long-term memory
                    if await self.ai_service.should_save_to_long_term(question):
                        await self.convo_manager.save_to_long_term(
                            message.author.id,
                            f"User stated: {question}",  # Store direct user statement
                            message
                        )

                    # Send the generated response to the user
                    if len(bot_response) > 2000:  # Handle Discord's character limit
                        for chunk in [
                            bot_response[i : i + 2000]  # Split message into chunks
                            for i in range(0, len(bot_response), 2000)
                        ]:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(bot_response)

            except Exception as e:
                print(f"Error handling message: {e}")
                await message.channel.send("⚡ Something went wrong. Please try again later!")


async def setup(bot: commands.Bot):
    """
    Asynchronous setup function to add this cog to the bot.
    """
    await bot.add_cog(MessageHandler(bot))