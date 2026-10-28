import anthropic
from tavily import TavilyClient
from config import ANTHROPIC_API_KEY, TAVILY_API_KEY, MODEL, SYSTEM_PROMPT, TOOLS

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

def perform_web_search(query: str):
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
    messages = [{"role": "user", "content": otazka}]
    all_sources = []

    response = claude.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS
    )

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "web_search":
                query = block.input.get("query")
                print(f"[SEARCH] Prohledávám web pro: '{query}'")
                search_results, sources = perform_web_search(query)
                all_sources.extend(sources)

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

            final_response = claude.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=TOOLS
            )

            text_blocks = [block.text for block in final_response.content if getattr(block, "type", None) == "text"]
            return ("".join(text_blocks) if text_blocks else "Nedařilo se zpracovat odpověď z vyhledávání."), all_sources

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return ("".join(text_blocks) if text_blocks else "Nedařilo se vygenerovat odpověď."), all_sources


async def get_profile_analysis(user_name: str, chat_history: str) -> str:
    system_prompt = (
        "Jsi sarkastický, vtipný, ale trefný AI analytik pro Discord server. "
        "Dostaneš vzorek zpráv od konkrétního uživatele. Tvým úkolem je vytvořit "
        "krátký, stručný, zábavný profil jeho osobnosti, stylu psaní, nálady nebo zvyků. "
        "Piš česky, používej neformální jazyk, strukturuj odpověď přehledně "
        "a na začátek každému uživateli přiřaď krátký originální 'Discord Titul'."
    )
    prompt = f"Zde jsou poslední zprávy uživatele {user_name}:\n{chat_history}\n\nUdělej jeho stručnou a zábavnou AI analýzu."

    response = claude.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(text_blocks) if text_blocks else "Nepodařilo se vygenerovat analýzu."


async def get_larp_response(persona: str, user_input: str) -> str:
    system_prompt = (
        f"Jsi zkušený LARP (Live Action Role Play) herec. "
        f"Tvým úkolem je plně se vžít do následující postavy a odpovídat uživateli POUZE v této roli. "
        f"Popis tvé postavy: {persona}\n\n"
        f"Pravidla:\n"
        f"- Reaguj autenticky, používej odpovídající tón, dialekt nebo slovník dle zadání.\n"
        f"- Nikdy nevystupuj z role a nemluv jako AI model."
        f"- Zanech LARP krátký a lehce s humorem a sarkasmem"
    )

    response = claude.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}]
    )

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(text_blocks) if text_blocks else "Postava ztratila řeč..."


async def translate_text(text: str, target_language: str) -> str:
    system_prompt = (
        "Jsi profesionální překladač pro Discord komunitu. "
        f"Přelož zadaný text přirozeně do jazyka: {target_language}.\n"
        "Pravidla:\n"
        "- Zachovej původní význam, tón, slang i formátování.\n"
        "- Vrať POUZE samotný přeložený text bez jakýchkoliv úvodních keců nebo uvozovek."
    )

    response = claude.messages.create(
        model=MODEL,
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": text}]
    )

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(text_blocks) if text_blocks else "Nepodařilo se vygenerovat překlad."


async def get_chat_reply(chat_history: list, current_user: str, latest_message: str) -> str:
    
    SEARCH = "[INTERNET]"

    # hledani na internetu pres tavily api
    web_search_results = ""

    # Kontext historie pro vygenerování přesného dotazu
    history_context = chat_history[:-1] if len(chat_history) > 1 else []
    formatted_context = ""
    for msg in history_context:
        formatted_context += f"{msg['author']}: {msg['content']}\n"

    search_query = None
    if tavily and latest_message:
        try:
            query_prompt = (
                "Jsi pomocník pro vyhledávání. Na základě kontextu chatu a poslední zprávy uživatele "
                "vymysli 1 krátký, přesný a efektivní vyhledávací dotaz pro vyhledávač v češtině nebo angličtině.\n"
                "Pokud zpráva NEVYŽADUJE vyhledávání na internetu (např. pozdrav, běžný pokec, názor nebo reakce, k níž nepotřebuješ data), napiš POUZE slovo 'NONE'.\n\n"
                f"Kontext konverzace:\n{formatted_context}\n"
                f"Poslední zpráva od {current_user}: {latest_message}\n\n"
                "Vyhledávací dotaz:"
            )

            query_response = claude.messages.create(
                model=MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": query_prompt}]
            )
            
            raw_query = query_response.content[0].text.strip()
            
            if raw_query and "NONE" not in raw_query.upper():
                search_query = raw_query

        except Exception as e:
            print(f"{SEARCH} Chyba při generování dotazu: {e}")

    if search_query:
        try:
            print(f"{SEARCH} Claude vytvořil dotaz: '{search_query}' (Původní zpráva: '{latest_message}')")
            tavily_res = tavily.search(query=search_query, max_results=3)
            results = tavily_res.get("results", [])
            if results:
                web_search_results = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
                print(f"{SEARCH} Načteno {len(results)} výsledků")
            else:
                print(f"{SEARCH} Nenačteny žádné výsledky.")
        except Exception as e:
            print(f"{SEARCH} Chyba při vyhledávání na webu v chatu: {e}")
    else:
        print(f"{SEARCH} Vyhledávání přeskočeno (není potřeba).")

    system_prompt = (
        "Jsi TwelveCorp, inteligentní, přátelský a lehce nad věcí člen Discord komunity. "
        "Uživatelé tě zmínili v chatu. Reaguj přirozeně, stručně a lidsky v češtině.\n"
        "PRAVIDLA:\n"
        "- Historie chatu níže slouží POUZE jako kontext, abys věděl, o čem se lidé v kanálu bavili.\n"
        "- NEROZEBÍREJ znovu staré otázky nebo témata z historie, která už byla zodpovězena.\n"
        "- Odpovídej VÝHRADNĚ na poslední (nejnovější) zprávu od uživatele.\n"
        "- Pokud jsou k dispozici výsledky z vyhledávání na webu, využij je k přesné a aktuální odpovědi.\n"
        "- Nepoužívej formální úvody, zdravení ani nadbytečné strukturování."
    )

    user_prompt = ""
    if formatted_context:
        user_prompt += f"Kontext předchozí konverzace v kanálu:\n---\n{formatted_context}---\n\n"
    
    if web_search_results:
        user_prompt += f"Aktuální informace z internetu k dotazu:\n---\n{web_search_results}\n---\n\n"

    user_prompt += f"Poslední zpráva od '{current_user}', na kterou musíš právě zareagovat: {latest_message}"

    response = claude.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(text_blocks) if text_blocks else "Ahoj!"