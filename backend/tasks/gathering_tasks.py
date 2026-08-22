from crewai import Task

def create_gathering_task(scout_agent, target_topic, competitor_name):
    """Creates the task for the Scout Agent to execute."""
    
    return Task(
        description=(
            f"1. Use the 'Live Web Search Tool' to find the latest news and announcements "
            f"regarding the competitor: '{competitor_name}'.\n"
            f"2. Use the 'Academic Research Tool' to find recent scientific papers "
            f"related to the technology: '{target_topic}'.\n"
            f"Gather all this raw data into a structured list."
        ),
        expected_output="A bulleted list containing raw news headlines, URLs, and scientific paper summaries.",
        agent=scout_agent
    )