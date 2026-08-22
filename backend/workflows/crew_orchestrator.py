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

# Resilient LLM Configuration
gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=GEMINI_KEY
)

def run_tracker(topic: str, competitor: str):
    """
    Executes the multi-agent competitor research workflow with resource-aware limits,
    loop detection, and fallback retry mechanisms (Task 5).
    """
    # 1. Instantiate Agents with Loop Caps (Deadlock/Loop Detection)
    scout = create_scout_agent()
    scout.llm = gemini_llm
    scout.max_iter = 8  # Protects against infinite tool loops

    analyst = create_analyst_agent()
    analyst.llm = gemini_llm
    analyst.max_iter = 8  # Protects against infinite tool loops

    # 2. Instantiate Tasks
    gather_task = create_gathering_task(scout, topic, competitor)
    analyze_task = create_analysis_task(analyst, gather_task, topic)

    # 3. Form Crew (Orchestration, Shared State, and Memory Management)
    ai_crew = Crew(
        agents=[scout, analyst],
        tasks=[gather_task, analyze_task],
        process=Process.sequential,
        memory=False,  # Keep false to protect your free tier quota limits
        max_rpm=15,    # Resource-aware execution constraint
        embedder={
            "provider": "google-generativeai",
            "config": {
                "model_name": "gemini-embedding-001",
                "api_key": GEMINI_KEY
            }
        }
    )

    print(f"\n🚀 Launching Agent Fleet: {competitor} | Topic: {topic}")

    # 4. Execution Loop with Autonomous Failure Recovery
    max_retries = 3
    retry_delay = 65  # Sufficient delay for Google API 429 quota replenishment

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