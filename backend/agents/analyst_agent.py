from crewai import Agent

def create_analyst_agent():
    """Creates and returns the Synthesizer/Analyst agent."""
    
    analyst_agent = Agent(
        role='Senior Intelligence Analyst',
        goal='Analyze raw research and news data to identify strategic threats, opportunities, and trends.',
        backstory='You are a seasoned corporate strategist. You excel at reading raw data, finding hidden connections between academic research and corporate news, and delivering concise, high-impact summaries.',
        allow_delegation=False,
        verbose=True
    )
    
    return analyst_agent