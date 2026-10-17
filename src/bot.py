import os
import discord
from discord import app_commands
from discord.ext import commands
import anthropic
from dotenv import load_dotenv

# Načtení proměnných z .env
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
        # Do volání jsme přidali parametr system=SYSTEM_PROMPT
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": otazka}
            ]
        )

        reply_text = response.content[0].text

        if len(reply_text) > 2000:
            reply_text = reply_text[:1997] + "..."

        await interaction.followup.send(f"**Otázka:** {otazka}\n\n{reply_text}")

    except Exception as e:
        print(f"Chyba při komunikaci s Claude API: {e}")
        await interaction.followup.send("Omlouvám se, něco se pokazilo.")


bot.run(DISCORD_TOKEN)