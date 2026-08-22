from crewai import Task

def create_analysis_task(analyst_agent, gathering_task, target_topic):
    """Creates the task for the Analyst Agent to synthesize the data."""
    
    return Task(
        description=(
            f"Review the raw data gathered about '{target_topic}'.\n"
            f"1. Discard any irrelevant or duplicate information.\n"
            f"2. Identify genuine trends and flag potential competitive threats.\n"
            f"3. Assign an Impact Score (1-10) to the top 3 most critical findings."
        ),
        expected_output="A structured markdown report with the top 3 insights, their impact scores, and a brief strategic recommendation.",
        agent=analyst_agent,
        context=[gathering_task] # This is crucial: It tells the Analyst to wait for the Scout's output
    )