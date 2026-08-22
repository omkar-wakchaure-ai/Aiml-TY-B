import os
import sys

from dotenv import load_dotenv

# Force load the environment variables (bypasses caching issues)
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    override=True,
)

# Ensure Python can find your workflows and agents folders
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.crew_orchestrator import run_tracker

if __name__ == "__main__":
    # Test execution block
    report = run_tracker(topic="Solid State Battery", competitor="Competitor X")
    print("\n====== FINAL INTELLIGENCE REPORT ======\n")
    print(report)