import asyncio
from duckduckgo_search import DDGS

async def quick_web_search(query: str, max_results: int = 5) -> str:
    """Fast, browser-less search for real-time news, facts, and weather."""
    def _search():
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No results found."
            
            formatted = []
            for r in results:
                formatted.append(f"Title: {r['title']}\nSnippet: {r['body']}")
            
            return "\n\n".join(formatted)
            
    try:
        return await asyncio.to_thread(_search)
    except Exception as e:
        return f"Quick search failed: {str(e)}"