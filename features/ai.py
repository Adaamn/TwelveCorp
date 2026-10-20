import discord
from discord import app_commands
from discord.ext import commands
from config import TITLE, EMBED_COLOR
from services import get_claude_response

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Zeptat se bota TwelveCorp na cokoliv")
    @app_commands.describe(otazka="Tvoje otázka pro TwelveCorp")
    async def ask_claude(self, interaction: discord.Interaction, otazka: str):
        await interaction.response.defer()
        user_name = interaction.user.display_name
        print(f"\n[SLASH (/ask) od: {user_name}] Otázka: {otazka}")

        try:
            reply_text, sources = await get_claude_response(otazka, max_tokens=800)
            print(f"[TwelveCorp] Odpověď: {reply_text}\n" + "-"*40)

            if len(reply_text) > 2000:
                reply_text = reply_text[:1997] + "..."

            embed = discord.Embed(title=TITLE, description=reply_text, color=EMBED_COLOR)
            if sources:
                formatted_sources = [f"🔗 [{s['title'][:37] + '...' if len(s['title']) > 40 else s['title']}]({s['url']})" for s in sources]
                embed.add_field(name="Použité zdroje", value=" | ".join(formatted_sources), inline=False)

            embed.set_footer(text=f"Otázka od: {user_name}", icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Původní otázka", value=otazka if len(otazka) <= 1024 else otazka[:1021] + "...", inline=False)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Chyba při komunikaci s Claude API (/ask): {e}")
            await interaction.followup.send("Omlouvám se, něco se pokazilo.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.user.mentioned_in(message):
            otazka = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            
            if not otazka:
                await message.reply("Co potřebuješ? Zeptej se na něco konkrétního.")
                return

            user_name = message.author.display_name
            print(f"\n[MENTION v chatu od: {user_name}] Otázka: {otazka}")

            async with message.channel.typing():
                try:
                    reply_text, sources = await get_claude_response(otazka, max_tokens=600)
                    print(f"[TwelveCorp] Odpověď na mention: {reply_text}\n" + "-"*40)

                    if len(reply_text) > 2000:
                        reply_text = reply_text[:1997] + "..."

                    embed = discord.Embed(title=TITLE, description=reply_text, color=EMBED_COLOR)
                    if sources:
                        formatted_sources = [f"🔗 [{s['title'][:37] + '...' if len(s['title']) > 40 else s['title']}]({s['url']})" for s in sources]
                        embed.add_field(name="Použité zdroje", value=" | ".join(formatted_sources), inline=False)

                    embed.set_footer(text=f"Otázka od: {user_name}", icon_url=message.author.display_avatar.url)
                    embed.add_field(name="Původní otázka", value=otazka if len(otazka) <= 1024 else otazka[:1021] + "...", inline=False)

                    await message.reply(embed=embed)

                except Exception as e:
                    print(f"Chyba při komunikaci s Claude API (mention): {e}")
                    await message.reply("Omlouvám se, něco se pokazilo.")

async def setup(bot):
    await bot.add_cog(AI(bot))