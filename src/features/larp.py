import discord
from discord import app_commands
from discord.ext import commands
from config import EMBED_COLOR
from services import get_larp_response

class Larp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="larp", description="Larpuj někoho/něco")
    @app_commands.describe(
        postava="Koho má bot larpovat? (např. Jan Ptáček z Pirkštejna)",
        zprava="Co postavě řekneš nebo jaká situace nastane"
    )
    async def larp_command(self, interaction: discord.Interaction, postava: str, zprava: str):
        await interaction.response.defer()

        print(f"\n[SLASH (/larp) od: {interaction.user.display_name}] Postava: '{postava}' | Zpráva: '{zprava}'")

        try:
            response_text = await get_larp_response(postava, zprava)

            embed = discord.Embed(
                title=f"🎭 LARP: {postava}",
                description=response_text,
                color=EMBED_COLOR
            )
            embed.add_field(name=f"💬 {interaction.user.display_name} říká:", value=zprava, inline=False)
            embed.set_footer(text=f"Požadavek od: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Chyba při LARP interakci: {e}")
            await interaction.followup.send("Omlouvám se, postava se zrovna ztratila v čase a prostoru.")

async def setup(bot):
    await bot.add_cog(Larp(bot))