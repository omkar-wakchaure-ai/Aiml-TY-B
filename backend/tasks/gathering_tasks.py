from crewai import Task

def create_gathering_task(scout_agent, target_topic, competitor_name):
    """Creates the task for the Scout Agent to execute."""
    
    return Task(
        description=(
            f"1. Use the 'Live Web Search Tool' to find the latest news and announcements "
            f"regarding the competitor: '{competitor_name}'.\n"
            f"2. Use the 'Academic Research Tool' to find recent scientific papers "
            f"related to the technology: '{target_topic}'.\n"
            f"Gather all this raw data into a structured list. For every item include "
            f"source, date when available, claim, evidence excerpt, and confidence. "
            f"If '{competitor_name}' or '{target_topic}' is too vague, report the ambiguity "
            f"and do not invent a target. Preserve tool errors for the recovery controller."
        ),
        expected_output="A structured evidence list with source, date, claim, excerpt, confidence, and explicit tool or data gaps.",
        agent=scout_agent
    )