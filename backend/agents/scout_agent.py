from crewai import Agent

# Fixed import paths to match your actual file names
from tools.web_search import search_competitor_news
from tools.arxiv_api import search_research_papers

def create_scout_agent():
    scout_agent = Agent(
        role='Data Scout',
        goal='Gather raw, factual data from the internet regarding competitors and scientific research.',
        backstory='You are an expert investigative researcher.',
        tools=[search_competitor_news, search_research_papers],
        allow_delegation=False,
        verbose=True
    )
    return scout_agent