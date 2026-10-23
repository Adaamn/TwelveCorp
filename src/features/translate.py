import discord
from discord.ext import commands
from config import EMBED_COLOR
from services import translate_text

FLAG_TO_LANGUAGE = {
    "🇬🇧": "Angličtina",
    "🇺🇸": "Angličtina",
    "🇨🇦": "Angličtina",
    "🇦🇺": "Angličtina",
    "🇪🇸": "Španělština",
    "🇲🇽": "Španělština",
    "🇧🇷": "Portugalština",
    "🇵🇹": "Portugalština",

    "🇨🇿": "Čeština",
    "🇸🇰": "Slovenština",
    "🇩🇪": "Němčina",
    "🇦🇹": "Němčina",
    "🇨🇭": "Němčina",
    "🇫🇷": "Francouzština",
    "🇮🇹": "Italština",
    "🇳🇱": "Holandština",
    "🇵🇱": "Polština",

    "🇸🇪": "Švédština",
    "🇳🇴": "Norsko",
    "🇩🇰": "Dánština",
    "🇫🇮": "Finština",
    "🇺🇦": "Ukrajinština",
    "🇭🇺": "Maďarština",
    "🇬🇷": "Řečtina",
    "🇭🇷": "Chorvatština",
    "🇷🇺": "Ruština",

    "🇯🇵": "Japonština",
    "🇰🇷": "Korejština",
    "🇨🇳": "Čínština",
    "🇻🇳": "Vietnamština",
    "🇹🇭": "Thajština",
    "🇹🇷": "Turečtina",
    "🇸🇦": "Arabština",
}

class Translator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        emoji_str = str(payload.emoji)

        if emoji_str not in FLAG_TO_LANGUAGE:
            return

        target_lang = FLAG_TO_LANGUAGE[emoji_str]

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception as e:
            print(f"Chyba při načítání zprávy pro překlad: {e}")
            return

        if not message.content:
            return

        print(f"\n[TRANSLATE] Překlad zprávy od {message.author.display_name} do {target_lang}")

        try:
            translated_content = await translate_text(message.content, target_lang)

            embed = discord.Embed(
                title=f"🌐 Překlad ({target_lang})",
                description=translated_content,
                color=EMBED_COLOR
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

            await message.reply(embed=embed, mention_author=False)

        except Exception as e:
            print(f"Chyba při překladu přes API: {e}")

async def setup(bot):
    await bot.add_cog(Translator(bot))