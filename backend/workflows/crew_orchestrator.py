import os
import time
from crewai import Crew, Process, LLM
from agents.scout_agent import create_scout_agent
from agents.analyst_agent import create_analyst_agent
from tasks.gathering_tasks import create_gathering_task
from tasks.analysis_tasks import create_analysis_task

# ============================================================
# GEMINI API CONFIGURATION
# ============================================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY is missing! Check your .env file.")

gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=GEMINI_KEY
)

def run_tracker(topic: str, competitor: str):
    # 1. Instantiate Agents with STRICT Loop Caps
    scout = create_scout_agent()
    scout.llm = gemini_llm
    scout.max_iter = 1  # <-- FORCE 1 SINGLE ACTION

    analyst = create_analyst_agent()
    analyst.llm = gemini_llm
    analyst.max_iter = 1  # <-- FORCE 1 SINGLE ACTION

    # 2. Instantiate Tasks
    gather_task = create_gathering_task(scout, topic, competitor)
    analyze_task = create_analysis_task(analyst, gather_task, topic)

    # 3. Form Crew (ULTRA-LIGHT CONFIGURATION)
    ai_crew = Crew(
        agents=[scout, analyst],
        tasks=[gather_task, analyze_task],
        process=Process.sequential,
        memory=False,  
        max_rpm=2   # Pace to 2 requests per minute
        # Embedder completely removed to stop hidden API calls
    )

    print(f"\n🚀 Launching Ultra-Light Fleet: {competitor} | Topic: {topic}")

    max_retries = 3
    retry_delay = 65  

    for attempt in range(max_retries):
        try:
            print(f"🔄 Execution Attempt {attempt + 1}/{max_retries}...")
            time.sleep(2)
            
            result = ai_crew.kickoff()
            print("✅ Workflow Successfully Completed!")
            return result

        except Exception as e:
            error_str = str(e)
            print(f"\n⚠️ Execution Encountered Error: {error_str}\n")

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    print(f"⏳ Quota limit reached. Pausing for {retry_delay}s to refill token bucket...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError("API Quota Exhausted. System paused to prevent service termination.")
            
            elif attempt < max_retries - 1:
                print(f"🔄 Retrying transient error in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            else:
                raise e