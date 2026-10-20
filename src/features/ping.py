import discord
from discord import app_commands
from discord.ext import commands
from config import TITLE, EMBED_COLOR

class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Zjistí latenci a odezvu bota")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        print(f"\n[SLASH (/ping) od: {interaction.user.display_name}] Latence: {latency}ms")

        embed = discord.Embed(
            title=TITLE,
            description=f"Odezva bota: **{latency} ms**",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Požadavek od: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Util(bot))