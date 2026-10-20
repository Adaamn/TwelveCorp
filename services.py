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