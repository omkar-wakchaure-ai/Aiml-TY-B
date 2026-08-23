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

## Task 7: Advanced Tracing & Observability

The orchestrator includes a dependency-free local flight recorder. Each route,
tool call, failed primary tool, fallback, verifier step, and analyst synthesis
creates a structured span with timestamp, agent, operation, latency, estimated
tokens, status, and diagnosis. The Tool Calling page displays and exports the
trace as JSON; the Orchestration page displays the same trace beside a
before/after optimization benchmark.

The adversarial regression intentionally fails the web tool and verifies that
the trace contains both the failed span and the fallback span. This provides a
reproducible root-cause diagnosis without requiring LangSmith credentials.
The benchmark values shown in the UI are reference targets; live trace latency
and estimated token values are captured per run for comparison.
