import os
import discord
from discord import app_commands
from discord.ext import commands
import anthropic
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

TITLE = "🤖 TwelveCorp"
EMBED_COLOR = discord.Color.from_str("#e6e6e6")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

SYSTEM_PROMPT = """
Jmenuješ se TwelveCorp. 
- Používej jednoduchá a srozumitelná vysvětlení.
- Pokud zadání není jasné, stručně se doptáš.
- Nevymýšlej si fakta. Pokud něco nevíš nebo nemáš aktuální data, použiij vyhledávací nástroj.
- Vynechávej zbytečné úvody, opakování a omáčku.
- Odpovídej neformálně jazykem kterým píše uživatel.
"""

# Definice nástroje pro vyhledávání na webu pro Claude API
TOOLS = [
    {
        "name": "web_search",
        "description": "Vyhledá aktuální informace na internetu. Použij, pokud se uživatel ptá na aktuální zprávy, výsledky zápasů, počasí nebo věci po roce 2024.",
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

def perform_web_search(query: str) -> str:
    """Funkce pro provedení vyhledávání přes Tavily API."""
    if not tavily:
        return "Vyhledávání na webu není dostupné (chybí TAVILY_API_KEY)."
    try:
        results = tavily.search(query=query, max_results=3)
        formatted_results = []
        for res in results.get("results", []):
            formatted_results.append(f"Titul: {res['title']}\nObsah: {res['content']}\nURL: {res['url']}")
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Chyba při vyhledávání: {e}"

async def get_claude_response(otazka: str, max_tokens: int = 800) -> str:
    """Zpracuje dotaz přes Claude API s možností automatického vyhledávání na webu."""
    messages = [{"role": "user", "content": otazka}]

    # 1. První volání Claudovi s nabídkou nástrojů
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS
    )

    # 2. Kontrola, zda si Claude vyžádal vyhledávání na webu
    if response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use.name
        tool_input = tool_use.input

        if tool_name == "web_search":
            query = tool_input.get("query")
            print(f"[SEARCH] Prohledávám web pro: '{query}'")
            search_results = perform_web_search(query)

            # Přidáme odpověď asistenta s požadavkem na tool a výsledek hledání do historie
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": search_results,
                    }
                ],
            })

            # 3. Druhé volání Claudovi s výsledky hledání
            final_response = claude.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=TOOLS
            )
            return final_response.content[0].text

    # Pokud vyhledávání nebylo potřeba, vrátíme přímou odpověď
    for block in response.content:
        if block.type == "text":
            return block.text

    return "Nedařilo se vygenerovat odpověď."


@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="@TwelveCorp | /ask")
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

    user_name = interaction.user.display_name
    print(f"\n[SLASH (/ask) od: {user_name}] Otázka: {otazka}")

    try:
        reply_text = await get_claude_response(otazka, max_tokens=800)
        print(f"[TwelveCorp] Odpověď: {reply_text}\n" + "-"*40)

        if len(reply_text) > 2000:
            reply_text = reply_text[:1997] + "..."

        embed = discord.Embed(
            title=TITLE,
            description=reply_text,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Otázka od: {user_name}", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Původní otázka", value=otazka if len(otazka) <= 1024 else otazka[:1021] + "...", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Chyba při komunikaci s Claude API (/ask): {e}")
        await interaction.followup.send("Omlouvám se, něco se pokazilo.")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        otazka = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not otazka:
            await message.reply("Copak potřebuješ? Zeptej se na něco konkrétního!")
            return

        user_name = message.author.display_name
        print(f"\n[MENTION v chatu od: {user_name}] Otázka: {otazka}")

        async with message.channel.typing():
            try:
                reply_text = await get_claude_response(otazka, max_tokens=600)
                print(f"[TwelveCorp] Odpověď na mention: {reply_text}\n" + "-"*40)

                if len(reply_text) > 2000:
                    reply_text = reply_text[:1997] + "..."

                embed = discord.Embed(
                    title=TITLE,
                    description=reply_text,
                    color=EMBED_COLOR
                )
                embed.set_footer(text=f"Otázka od: {user_name}", icon_url=message.author.display_avatar.url)
                embed.add_field(
                    name="Původní otázka", 
                    value=otazka if len(otazka) <= 1024 else otazka[:1021] + "...", 
                    inline=False
                )

                await message.reply(embed=embed)

            except Exception as e:
                print(f"Chyba při komunikaci s Claude API (mention): {e}")
                await message.reply("Omlouvám se, něco se pokazilo.")

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)