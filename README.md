## Task 5: Agent Framework

This project uses **CrewAI** because it already provides role-based agents,
tool execution, task context, agent memory, and LLM-backed delegation. The
custom `DynamicCrewOrchestrator` in `backend/workflows/crew_orchestrator.py`
owns the control loop around CrewAI so the system is not a fixed sequential
workflow.

Implemented capabilities:

- Dynamic planning and adaptive task decomposition through shared `ResearchState`.
- Multi-agent orchestration with parallel web, research, and patent branches.
- Conditional routing between collection, verification, analysis, and finish states.
- Shared state, file-backed checkpointing, and resume support.
- Failure recovery with per-tool fallback routing and bounded resource budgets.
- Conflicting-evidence detection, confidence scoring, and uncertainty-aware verification.
- Self-evaluation, hypothesis tracking, repeated-route/deadlock detection, and autonomous replanning.
- Adversarial live-style test in `backend/workflows/test_crew_orchestrator.py` that simulates a failed web tool and contradictory evidence.

Run the adversarial test with:

```text
python -m unittest backend.workflows.test_crew_orchestrator -v
```
