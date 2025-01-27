import discord
from discord.ext import commands
from config import settings, constants
from bot.models.conversation import ConversationManager
from bot.services.ai import AIService
from bot.services.search import SearchService


class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.convo_manager = ConversationManager()
        self.ai_service = AIService()
        self.search_service = SearchService()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message):
            question = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            if not question:
                return

            try:
                async with message.channel.typing():
                    if await self.ai_service.should_search_web(question):
                        search_result = await self.search_service.search_web(question)
                        if not search_result:
                            await message.channel.send("*looks embarrassed* Connection issues! Try again?")
                            return
                        
                        messages = [{
                            "role": "user",
                            "content": f"Web info: {search_result}\nUser question: {question}"
                        }]
                    else:
                        messages = self.convo_manager.get_history(message.author.id) + [
                            {"role": "user", "content": question}
                        ]

                    response = await self.ai_service.generate_response(
                        messages=messages,
                        system_prompt=constants.SystemMessages.VIGIL_PERSONALITY
                    )
                    answer = response.content[0].text
                    
                    self.convo_manager.add_message(message.author.id, question, answer)
                    
                    if len(answer) > 2000:
                        for chunk in [answer[i:i+2000] for i in range(0, len(answer), 2000)]:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(answer)

            except Exception as e:
                print(f"Message handling error: {e}")
                await message.channel.send("*system glitches* Rebooting circuits...")

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))