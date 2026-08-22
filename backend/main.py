import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.crew_orchestrator import run_tracker


if __name__ == "__main__":
    report = run_tracker(topic="Solid State Battery", competitor="Competitor X")
    print("\n====== FINAL INTELLIGENCE REPORT ======\n")
    print(report)
