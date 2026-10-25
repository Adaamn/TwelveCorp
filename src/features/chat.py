import discord
from discord.ext import commands
from services import get_chat_reply

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            clean_current_message = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            
            print(f"\n[CHAT MENTION] Od uživatele: {message.author.display_name} | Zpráva: {clean_current_message}")

            async with message.channel.typing():
                try:
                    chat_history = []
                    async for msg in message.channel.history(limit=10):
                        if msg.content and not msg.author.bot:
                            clean_content = msg.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
                            chat_history.append({
                                "author": msg.author.display_name,
                                "content": clean_content
                            })

                    chat_history.reverse()

                    reply_text = await get_chat_reply(
                        chat_history=chat_history,
                        current_user=message.author.display_name,
                        latest_message=clean_current_message
                    )

                    await message.reply(reply_text, mention_author=False)

                except Exception as e:
                    print(f"Chyba při zpracování AI chatu: {e}")
                    await message.reply("Promiň, něco se pokazilo.", mention_author=False)

async def setup(bot):
    await bot.add_cog(Chat(bot))