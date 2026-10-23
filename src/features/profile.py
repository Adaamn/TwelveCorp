import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from services import get_profile_analysis

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Zanalyzuje styl psaní a chování uživatele na základě jeho zpráv")
    @app_commands.describe(uzivatel="Uživatel, kterého chceš zanalyzovat")
    async def profile_analysis(self, interaction: discord.Interaction, uzivatel: discord.Member = None):
        target = uzivatel or interaction.user
        await interaction.response.defer()

        user_name = target.display_name
        print(f"\n[SLASH (/profile) od: {interaction.user.display_name}] Analýza uživatele: {user_name}")

        messages_text = []
        async for message in interaction.channel.history(limit=150):
            if message.author.id == target.id and message.content:
                messages_text.append(message.content)

        if not messages_text:
            print(f"Uživatel {user_name} neposlal žádné zprávy.")
            await interaction.followup.send(f"⚠️ V tomto kanálu jsem nenašel žádné nedávné zprávy od uživatele {user_name}.")
            return

        # max 50 zprav kvuli tokenum
        recent_messages = messages_text[:50]
        combined_text = "\n".join([f"- {msg}" for msg in recent_messages])

        try:
            analysis_result = await get_profile_analysis(user_name, combined_text)

            embed = discord.Embed(
                title=f"🕵️‍♂️ Analýza profilu: {user_name}",
                description=analysis_result,
                color=EMBED_COLOR
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.set_footer(text=f"Požadavek od: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Chyba při analýze profilu: {e}")
            await interaction.followup.send("Omlouvám se, při generování profilu nastala chyba.")

async def setup(bot):
    await bot.add_cog(Profile(bot))