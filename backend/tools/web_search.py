from crewai.tools import tool
from duckduckgo_search import DDGS

@tool("Live Web Search Tool")
def search_competitor_news(query: str) -> str:
    """
    Use this tool to search the live internet for recent news, 
    competitor announcements, or general company updates.
    """
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return str(results)
    except Exception as e:
        return f"Search error occurred: {str(e)}"