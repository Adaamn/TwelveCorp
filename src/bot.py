import os
import discord
from discord import app_commands
from discord.ext import commands
import anthropic
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
Jmenuješ se TwelveTron. 
- Používej jednoduchá a srozumitelná vysvětlení.
- Pokud zadání není jasné, stručně se doptáš.
- Nevymýšlej si fakta. Pokud něco nevíš, přiznej to.
- Vynechávej zbytečné úvody, opakování a omáčku.
- Odpovídej neformálně jazykem kterým píše uživatel
"""


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Načteno {len(synced)} slash příkazů.")
    except Exception as e:
        print(f"Chyba při synchronizaci příkazů: {e}")

    print(f"Bot {bot.user} je připraven k použití!")


@bot.tree.command(name="ask", description="Zeptat se bota TwelveTron na cokoliv")
@app_commands.describe(otazka="Tvoje otázka pro TwelveTrona")
async def ask_claude(interaction: discord.Interaction, otazka: str):
    await interaction.response.defer()

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": otazka}
            ]
        )

        reply_text = response.content[0].text

        if len(reply_text) > 4000:
            reply_text = reply_text[:3997] + "..."

        embed = discord.Embed(
            title="🤖 TwelveTron AI",
            description=reply_text,
            color=discord.Color.blurple()
        )
        
        embed.insert_field_at(
            index=0, 
            name=f"💬 Otázka od {interaction.user.display_name}", 
            value=otazka, 
            inline=False
        )
        
        embed.set_footer(text="TwelveCorp AI Assistant")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Chyba při komunikaci s API: {e}")
        await interaction.followup.send("Omlouvám se, něco se pokazilo.")


bot.run(DISCORD_TOKEN)