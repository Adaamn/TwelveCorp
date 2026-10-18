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
Jmenuješ se TwelveCorp. 
- Používej jednoduchá a srozumitelná vysvětlení.
- Pokud zadání není jasné, stručně se doptáš.
- Nevymýšlej si fakta. Pokud něco nevíš, přiznej to.
- Vynechávej zbytečné úvody, opakování a omáčku.
- Odpovídej neformálně jazykem kterým píše uživatel
"""

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="/ask")
    await bot.change_presence(activity=activity)

    try:
        synced = await bot.tree.sync()
        print(f"Načteno {len(synced)} slash příkazů.")
    except Exception as e:
        print(f"Chyba při synchronizaci příkazů: {e}")

    print(f"Bot {bot.user} je připraven k použití!")

@bot.tree.command(name="ask", description="Zeptat se bota TwelveCorp na cokoliv")
@app_commands.describe(otazka="Tvoje otázka pro TwelveCorp")
async def ask_claude(interaction: discord.Interaction, otazka: str):
    await interaction.response.defer()

    # Logování příchozí otázky
    user_name = interaction.user.display_name
    print(f"\n[ÚČET: {user_name}] Otázka: {otazka}")

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

        # Logování vygenerované odpovědi
        print(f"[TwelveCorp] Odpověď: {reply_text}\n" + "-"*40)

        if len(reply_text) > 1024:
            reply_text = reply_text[:1021] + "..."

        embed = discord.Embed(
            title="🤖 TwelveCorp AI",
            description=reply_text,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Otázka od: {user_name}", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Původní otázka", value=otazka, inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Chyba při komunikaci s Claude API: {e}")
        await interaction.followup.send("Omlouvám se, něco se pokazilo.")


bot.run(DISCORD_TOKEN)