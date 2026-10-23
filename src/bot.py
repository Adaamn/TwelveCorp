from art import text2art
import discord
from discord.ext import commands
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="@TwelveCorp | /ask")
    await bot.change_presence(activity=activity)

    try:
        await bot.load_extension("features.ai")
        await bot.load_extension("features.ping")
        await bot.load_extension("features.profile")
        synced = await bot.tree.sync()
        print(f"Načteno {len(synced)} slash příkazů a cogs.")
    except Exception as e:
        print(f"Chyba při inicializaci bota: {e}")

    print(text2art("TwelveCorp"))
    print(f"Bot {bot.user} je připraven k použití!")

bot.run(DISCORD_TOKEN)