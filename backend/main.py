import os
import sys
import time

from dotenv import load_dotenv
from crewai import Crew, Process, LLM

from agents.scout_agent import create_scout_agent
from agents.analyst_agent import create_analyst_agent
from tasks.gathering_tasks import create_gathering_task
from tasks.analysis_tasks import create_analysis_task

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# GEMINI API CONFIGURATION
# ============================================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing!\n"
        "Please make sure your .env file contains your GEMINI_API_KEY."
    )

# ============================================================
# CREATE GEMINI LLM
# ============================================================
gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=GEMINI_KEY
)

# ============================================================
# RUN COMPETITOR TRACKER
# ============================================================
def run_tracker(topic, competitor):

    # 1. CREATE SCOUT AGENT
    scout = create_scout_agent()
    scout.llm = gemini_llm

    # 2. CREATE ANALYST AGENT
    analyst = create_analyst_agent()
    analyst.llm = gemini_llm

    # 3. CREATE TASKS
    gather_task = create_gathering_task(scout, topic, competitor)
    analyze_task = create_analysis_task(analyst, gather_task, topic)

    # 4. CREATE CREW
    ai_crew = Crew(
        agents=[scout, analyst],
        tasks=[gather_task, analyze_task],
        process=Process.sequential,
        memory=True, 
        max_rpm=10,  # Limits requests to prevent 429 quota errors
        embedder={
            "provider": "google-generativeai",
            "config": {
                "model_name": "gemini-embedding-001",
                "api_key": GEMINI_KEY
            }
        }
    )

    # 5. START AGENT WORKFLOW
    print("\n====================================================")
    print("🚀 STARTING RESEARCH & COMPETITOR AGENT")
    print("====================================================")
    print(f"📌 Topic      : {topic}")
    print(f"🏢 Competitor : {competitor}")
    print(f"🤖 Provider   : Google Gemini")
    print(f"🧠 Model      : gemini-3.6-flash")
    print("====================================================\n")

    # 6. RETRY CONFIGURATION
    max_retries = 3
    retry_delay = 20

    # 7. RUN CREW
    for attempt in range(max_retries):
        try:
            print(f"🔄 Running attempt {attempt + 1}/{max_retries}...")
            time.sleep(2)
            
            result = ai_crew.kickoff()
            
            print("\n====================================================")
            print("✅ AGENT WORKFLOW COMPLETED")
            print("====================================================")
            return result

        except Exception as e:
            error_str = str(e)
            print("\n❌ ERROR WHILE RUNNING AGENTS")
            print("----------------------------------------------------")
            print(error_str)
            print("----------------------------------------------------")

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    print(f"\n⚠️ Rate limit detected. ⏳ Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError(
                        "\nGoogle API quota limit reached (429).\n"
                        "Please wait 1 minute for your quota to refill, then try again."
                    )
            raise

if __name__ == "__main__":
    final_report = run_tracker(topic="Solid State Battery", competitor="Competitor X")
    print("\n\n====================================================")
    print("          FINAL INTELLIGENCE REPORT")
    print("====================================================\n")
    print(final_report)
    print("\n====================================================")
    print("                END OF REPORT")
    print("====================================================")