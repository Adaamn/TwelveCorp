import os
import datetime
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
MODEL="claude-sonnet-5-5"

TITLE = "🤖 TwelveCorp"
EMBED_COLOR = discord.Color.from_str("#e6e6e6")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

CURRENT_YEAR = datetime.datetime.now().year
SYSTEM_PROMPT = f"""
Jmenuješ se TwelveCorp. Dnešní rok je {CURRENT_YEAR}.
- Používej jednoduchá a srozumitelná vysvětlení.
- Pokud zadání není jasné, stručně se doptáš.
- Nevymýšlej si fakta. Pokud něco nevíš nebo nemáš aktuální data, použij vyhledávací nástroj.
- Vynechávej zbytečné úvody, opakování a omáčku.
- Odpovídej neformálně jazykem kterým píše uživatel.
"""

# nastroje pro claude api
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

def perform_web_search(query: str):
    """Funkce pro provedení vyhledávání přes Tavily API (max 2 výsledky pro úsporu tokenů)."""
    if not tavily:
        return "Vyhledávání na webu není dostupné (chybí TAVILY_API_KEY).", []
    try:
        results = tavily.search(query=query, max_results=2)
        formatted_results = []
        sources = []
        for res in results.get("results", []):
            formatted_results.append(f"Titul: {res['title']}\nObsah: {res['content']}\nURL: {res['url']}")
            if res.get('url'):
                sources.append({"title": res.get('title', 'Zdroj'), "url": res['url']})
        return ("\n\n".join(formatted_results) if formatted_results else "Žádné výsledky nenalezeny."), sources
    except Exception as e:
        return f"Chyba při vyhledávání: {e}", []

async def get_claude_response(otazka: str, max_tokens: int = 800):
    """Úsporné zpracování dotazu přes Claude API s max. 1 vyhledáváním."""
    messages = [{"role": "user", "content": otazka}]
    sources = []

    # 1. call claudovi s nabidkou tools
    response = claude.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS
    )

    # 2. kontrola jestli si claude api vyzadal vyhledani na webu
    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "web_search":
                query = block.input.get("query")
                print(f"[SEARCH] Prohledávám web pro: '{query}'")
                search_results, sources = perform_web_search(query)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": search_results,
                })

        if tool_results:
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # 3. druhy a finální call claudovi s výsledky
            final_response = claude.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=messages
            )

            text_blocks = [block.text for block in final_response.content if getattr(block, "type", None) == "text"]
            return ("".join(text_blocks) if text_blocks else "Nedařilo se zpracovat odpověď z vyhledávání."), sources

    # Pokud vyhledávání nebylo potřeba
    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return ("".join(text_blocks) if text_blocks else "Nedařilo se vygenerovat odpověď."), sources


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
        reply_text, sources = await get_claude_response(otazka, max_tokens=800)
        print(f"[TwelveCorp] Odpověď: {reply_text}\n" + "-"*40)

        if len(reply_text) > 2000:
            reply_text = reply_text[:1997] + "..."

        embed = discord.Embed(
            title=TITLE,
            description=reply_text,
            color=EMBED_COLOR
        )
        if sources:
            formatted_sources = [f"🔗 [{s['title'][:37] + '...' if len(s['title']) > 40 else s['title']}]({s['url']})" for s in sources]
            embed.add_field(name="Použité zdroje", value=" | ".join(formatted_sources), inline=False)

        embed.set_footer(text=f"Otázka od: {user_name}", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Původní otázka", value=otazka if len(otazka) <= 1024 else otazka[:1021] + "...", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Chyba při komunikaci s Claude API (/ask): {e}")
        await interaction.followup.send("Omlouvám se, něco se pokazilo.")


@bot.tree.command(name="ping", description="Zjistí latenci a odezvu bota")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    print(f"\n[SLASH (/ping) od: {interaction.user.display_name}] Latence: {latency}ms")

    embed = discord.Embed(
        title=TITLE,
        description=f"Odezva bota: **{latency} ms**",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Požadavek od: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        otazka = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not otazka:
            await message.reply("Co potřebuješ? Zeptej se na něco konkrétního.")
            return

        user_name = message.author.display_name
        print(f"\n[MENTION v chatu od: {user_name}] Otázka: {otazka}")

        async with message.channel.typing():
            try:
                reply_text, sources = await get_claude_response(otazka, max_tokens=600)
                print(f"[TwelveCorp] Odpověď na mention: {reply_text}\n" + "-"*40)

                if len(reply_text) > 2000:
                    reply_text = reply_text[:1997] + "..."

                embed = discord.Embed(
                    title=TITLE,
                    description=reply_text,
                    color=EMBED_COLOR
                )
                if sources:
                    formatted_sources = [f"🔗 [{s['title'][:37] + '...' if len(s['title']) > 40 else s['title']}]({s['url']})" for s in sources]
                    embed.add_field(name="Použité zdroje", value=" | ".join(formatted_sources), inline=False)

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