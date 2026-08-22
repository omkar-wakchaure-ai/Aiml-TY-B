import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure Python adds backend directory to search path
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

    # 4. Execute with Automatic Retry Logic for 429 Quotas
    print(f"🚀 Launching Agent Fleet with Gemini for {competitor} in {topic}...")
    
    max_retries = 3
    retry_delay = 15  # seconds to wait if rate-limited
    
    for attempt in range(max_retries):
        try:
            time.sleep(2)  # Buffer before kickoff
            result = ai_crew.kickoff()
            return result
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    print(f"⚠️ Rate limit hit (429). Waiting {retry_delay} seconds before retry {attempt + 2}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError(
                        "API Quota Limit Reached (429). The free tier is temporarily rate-limiting requests. "
                        "Please wait 1 minute for your quota token bucket to refill, then click 'Launch Agent Fleet' again."
                    )
            else:
                raise e

if __name__ == "__main__":
    final_report = run_tracker(topic="Solid State Battery", competitor="Competitor X")
    print("\n\n====== FINAL INTELLIGENCE REPORT ======\n")
    print(final_report)