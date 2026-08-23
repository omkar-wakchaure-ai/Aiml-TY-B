from crewai import Agent
try:
    from tools.web_search import search_competitor_news
    from tools.arxiv_api import search_research_papers
except ModuleNotFoundError:
    from ..tools.web_search import search_competitor_news
    from ..tools.arxiv_api import search_research_papers

def create_scout_agent():
    return Agent(
        role='Data Scout and Evidence Collector',
        goal=(
            'Gather verifiable competitor and technology evidence from live tools. '
            'Choose tools based on the research question, preserve source URLs and dates, '
            'and report missing, ambiguous, or failed sources without inventing data.'
        ),
        backstory=(
            'You are a careful OSINT researcher. Every finding must include its source, '
            'a concise claim, and a confidence estimate. Separate observed facts from '
            'inference, mark contradictory results explicitly, and stop when the target '
            'is too vague to research reliably. Never fill gaps with plausible guesses.'
        ),
        tools=[search_competitor_news, search_research_papers],
        verbose=True,
        max_iter=2,
        allow_delegation=False,
    )