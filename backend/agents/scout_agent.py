from crewai import Agent
try:
    from tools.web_search import search_competitor_news
    from tools.arxiv_api import search_research_papers
except ModuleNotFoundError:
    from ..tools.web_search import search_competitor_news
    from ..tools.arxiv_api import search_research_papers

def create_scout_agent():
    return Agent(
        role='Data Scout',
        goal='Gather raw news and recent academic research papers on competitors and technologies.',
        backstory='An expert in OSINT and technical literature review, specialized in finding raw intelligence.',
        tools=[search_competitor_news, search_research_papers],
        verbose=True
    )