import os
import sys
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Ensure Python adds the backend directory to its search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crewai import Crew, Process, LLM
from agents.scout_agent import create_scout_agent
from agents.analyst_agent import create_analyst_agent
from tasks.gathering_tasks import create_gathering_task
from tasks.analysis_tasks import create_analysis_task

# --- GEMINI API KEY CONFIGURATION ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY is missing! Make sure you have a .env file with your key.")

# Define the active Gemini model for CrewAI
gemini_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_KEY
)

def run_tracker(topic, competitor):
    # 1. Instantiate the Agents and assign the Gemini LLM
    scout = create_scout_agent()
    scout.llm = gemini_llm
    
    analyst = create_analyst_agent()
    analyst.llm = gemini_llm

    # 2. Instantiate the Tasks
    gather_task = create_gathering_task(scout, topic, competitor)
    analyze_task = create_analysis_task(analyst, gather_task, topic)

    # 3. Form the Crew
    ai_crew = Crew(
        agents=[scout, analyst],
        tasks=[gather_task, analyze_task],
        process=Process.sequential  # Runs Scout first, then Analyst
    )

    # 4. Execute the Workflow
    print(f"🚀 Launching Agent Fleet with Gemini for {competitor} in {topic}...")
    result = ai_crew.kickoff()
    
    return result

if __name__ == "__main__":
    # Test the pipeline directly in the terminal
    final_report = run_tracker(topic="Solid State Battery", competitor="Competitor X")
    print("\n\n====== FINAL INTELLIGENCE REPORT ======\n")
    print(final_report)