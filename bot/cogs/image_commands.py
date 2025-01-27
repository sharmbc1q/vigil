import discord
from discord.ext import commands
import httpx
import asyncio
from discord import app_commands
from config import settings



class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="imagine", description="Generate an image using Leonardo AI")
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        try:
            headers = {
                "Authorization": f"Bearer {settings.LEONARDO_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                # Start generation
                generation_response = await client.post(
                    "https://cloud.leonardo.ai/api/rest/v1/generations",
                    json={
                        "height": 512,
                        "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
                        "prompt": prompt,
                        "width": 512,
                        "num_images": 1
                    },
                    headers=headers
                )

                if generation_response.status_code != 200:
                    await interaction.followup.send("❌ Failed to start generation!")
                    return

                generation_id = generation_response.json().get('sdGenerationJob', {}).get('generationId')
                if not generation_id:
                    await interaction.followup.send("🚫 No generation ID received")
                    return

                # Poll for completion with better error handling
                status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                max_attempts = 30  # 30 attempts * 10 seconds = 5 minute timeout
                success = False

                for _ in range(max_attempts):
                    try:
                        status_response = await client.get(status_url, headers=headers)
                        status_data = status_response.json()
                        
                        status = status_data.get("generations_by_pk", {}).get("status")
                        
                        if status == "FAILED":
                            await interaction.followup.send("❌ Image generation failed on Leonardo's side")
                            return
                            
                        if status == "COMPLETE":
                            images = status_data.get("generations_by_pk", {}).get("generated_images", [])
                            if images:
                                image_url = images[0].get('url')
                                if image_url:
                                    embed = discord.Embed(title=prompt[:256], description="")
                                    embed.set_image(url=image_url)
                                    await interaction.followup.send(embed=embed)
                                    success = True
                                    break
                        await asyncio.sleep(10)  # Check every 10 seconds
                    
                    except Exception as e:
                        print(f"Status check error: {e}")
                        await asyncio.sleep(10)
                        continue

                if not success:
                    await interaction.followup.send(f"⏰ Generation timed out, but check later: https://leonardo.ai/generations/{generation_id}")

        except Exception as e:
            print(f"Image command error: {str(e)}")
            await interaction.followup.send("⚡ Generation failed unexpectedly!")

async def setup(bot):
    await bot.add_cog(ImageCommands(bot))