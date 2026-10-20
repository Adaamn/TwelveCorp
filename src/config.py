import os
import datetime
import discord
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MODEL = "claude-sonnet-5-5"

TITLE = "🤖 TwelveCorp"
EMBED_COLOR = discord.Color.from_str("#e6e6e6")

CURRENT_YEAR = datetime.datetime.now().year
SYSTEM_PROMPT = f"""
Jmenuješ se TwelveCorp. Dnešní rok je {CURRENT_YEAR}.
- Používej jednoduchá a srozumitelná vysvětlení.
- Pokud zadání není jasné, stručně se doptáš.
- Nevymýšlej si fakta. Pokud něco nevíš nebo nemáš aktuální data, použij vyhledávací nástroj.
- Vynechávej zbytečné úvody, opakování a omáčku.
- Odpovídej neformálně jazykem kterým píše uživatel.
"""

TOOLS = [
    {
        "name": "web_search",
        "description": "Vyhledá aktuální informace na internetu. Použij, pokud se uživatel ptá na aktuální zprávy, výsledky zápasů, počasí nebo čerstvá data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Vyhledávací dotaz v češtině nebo angličtině"
                }
            },
            "required": ["query"]
        }
    }
]