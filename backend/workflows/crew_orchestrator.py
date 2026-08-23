import hashlib
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from agents.scout_agent import create_scout_agent
    from agents.analyst_agent import create_analyst_agent
    from tasks.gathering_tasks import create_gathering_task
    from tasks.analysis_tasks import create_analysis_task
    from memory.rag_utils import get_memory_context_for_question, get_historical_context, is_duplicate_insight, store_new_insight
except ModuleNotFoundError:
    from ..agents.scout_agent import create_scout_agent
    from ..agents.analyst_agent import create_analyst_agent
    from ..tasks.gathering_tasks import create_gathering_task
    from ..tasks.analysis_tasks import create_analysis_task
    from ..memory.rag_utils import get_memory_context_for_question, get_historical_context, is_duplicate_insight, store_new_insight


@dataclass
class Evidence:
    claim: str
    source: str
    content: str
    confidence: float = 0.5
    # Original, un-penalized confidence. Conflict resolution derives the
    # working `confidence` from this every time it runs, instead of
    # repeatedly halving whatever `confidence` happened to be last round.
    # That keeps conflict penalties idempotent across multiple verify passes.
    base_confidence: Optional[float] = None

    def __post_init__(self):
        if self.base_confidence is None:
            self.base_confidence = self.confidence


@dataclass
class ResearchState:
    topic: str
    competitor: str
    budget: int = 6
    plan: List[str] = field(default_factory=lambda: ["web", "research", "patent"])
    completed: List[str] = field(default_factory=list)
    failed: Dict[str, str] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    confidence: float = 0.0
    report: str = ""
    route_history: List[str] = field(default_factory=list)
    checkpoints: int = 0


class JsonCheckpointStore:
    def __init__(self, directory: Optional[Path] = None):
        self.directory = directory or Path(os.getenv("CHECKPOINT_DIR", "checkpoints"))

    def save(self, state: ResearchState):
        self.directory.mkdir(parents=True, exist_ok=True)
        data = asdict(state)
        data["saved_at"] = datetime.now(timezone.utc).isoformat()
        target = self.directory / f"{self._key(state.topic, state.competitor)}.json"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, topic: str, competitor: str):
        target = self.directory / f"{self._key(topic, competitor)}.json"
        if not target.exists():
            return None
        data = json.loads(target.read_text(encoding="utf-8"))
        data.pop("saved_at", None)
        data["evidence"] = [Evidence(**item) for item in data.get("evidence", [])]
        return ResearchState(**data)

    @staticmethod
    def _key(topic: str, competitor: str):
        return hashlib.sha256(f"{topic.lower()}::{competitor.lower()}".encode()).hexdigest()[:20]


last_run_telemetry = []
last_confidence = 0
last_metrics = {"agents": 2, "tools": 0, "checkpoints": 0, "recoveries": 0, "routes": 0}
last_trace = []
trace_lock = threading.Lock()


def get_last_run_telemetry():
    return list(last_run_telemetry)


def get_last_confidence():
    return last_confidence


def get_last_metrics():
    return dict(last_metrics)


def get_last_trace():
    with trace_lock:
        return [dict(span) for span in last_trace]


def ask_agents(question: str, topic: str = "", competitor: str = "") -> str:
    """Answer from memory first, then research and refresh memory when needed."""
    question = question.strip()
    if not question:
        return "Please enter a question for the agent team."

    historical_context = get_memory_context_for_question(question, topic, competitor)
    if topic and competitor:
        checkpoint = JsonCheckpointStore().load(topic, competitor)
        if checkpoint:
            checkpoint_context = "\n\n".join(
                [
                    f"Claim: {item.claim}\nSource: {item.source}\nEvidence: {item.content}\nConfidence: {item.confidence:.0%}"
                    for item in checkpoint.evidence
                ]
            )
            if checkpoint.report:
                checkpoint_context += f"\n\nExecutive briefing:\n{checkpoint.report}"
            if checkpoint_context:
                historical_context = f"{historical_context}\n\nMission checkpoint:\n{checkpoint_context}"
    ignored_terms = {
        "about", "which", "what", "where", "when", "specific", "regarding",
        "highlighted", "developments", "information", "question", "evidence",
    }
    question_terms = {
        term.lower().strip(".,?!()")
        for term in question.split()
        if len(term.strip(".,?!()")) > 4 and term.lower().strip(".,?!()") not in ignored_terms
    }
    context_terms = set(re.findall(r"[a-zA-Z][a-zA-Z-]{4,}", historical_context.lower()))
    direct_support = len(question_terms & context_terms) >= 2
    if not direct_support:
        last_run_telemetry.append("MEMORY QA // no direct support found; launching targeted research fallback")
        targeted_report = DynamicCrewOrchestrator().run(
            topic=question,
            competitor=competitor or "Target Entity",
            budget=5,
        )
        historical_context = get_memory_context_for_question(question, topic, competitor)
        historical_context += f"\n\nTargeted research result:\n{targeted_report}"
    if historical_context == "No past historical data found on this topic.":
        return "Low Confidence / Insufficient Data: no relevant memory was found, and targeted research could not provide evidence."

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing")

    from crewai import Crew, LLM, Process, Task

    analyst = create_analyst_agent()
    analyst.llm = LLM(
        model=os.getenv("OPENROUTER_MODEL", "openrouter/openai/gpt-4o-mini"),
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    analyst.max_iter = 2
    task = Task(
        description=(
            f"Answer this follow-up question: '{question}'.\n\n"
            f"Retrieved memory:\n{historical_context}\n\n"
            "Use only the retrieved memory. Cite the relevant source text when possible. "
            "If memory is contradictory, explain the conflict and lower confidence. "
            "If memory does not support an answer, output exactly: "
            "Low Confidence / Insufficient Data. Never guess or use outside knowledge."
        ),
        expected_output="A concise, source-grounded answer with a confidence level or the required insufficient-data warning.",
        agent=analyst,
    )
    started = time.perf_counter()
    result = Crew(agents=[analyst], tasks=[task], process=Process.sequential, memory=False, max_rpm=15).kickoff()
    answer = str(result.raw) if hasattr(result, "raw") else str(result)
    last_run_telemetry.append(f"MEMORY QA // retrieved context and answered in {round((time.perf_counter() - started) * 1000)}ms")
    return answer


def _record_trace(agent, operation, started, status, detail="", tokens=0):
    span = {
        "Timestamp": time.strftime("%H:%M:%S"),
        "Agent": agent,
        "Operation": operation,
        "Latency (ms)": round((time.perf_counter() - started) * 1000),
        "Tokens (est.)": tokens,
        "Status": status,
        "Detail": detail,
    }
    with trace_lock:
        last_trace.append(span)
    return span


class DynamicCrewOrchestrator:
    fallbacks = {"web": "research", "research": "patent", "patent": "web"}

    def __init__(self, executor: Optional[Callable] = None, checkpoint_store=None, max_rounds=6, max_parallel=3):
        self.executor = executor or self._crewai_executor
        self.checkpoints = checkpoint_store or JsonCheckpointStore()
        self.max_rounds = max_rounds
        self.max_parallel = max_parallel

    def run(self, topic: str, competitor: str, budget=6):
        global last_run_telemetry, last_confidence, last_metrics, last_trace
        state = self.checkpoints.load(topic, competitor) or ResearchState(topic, competitor, budget)
        last_run_telemetry = [f"MISSION // {competitor} // {topic}"]
        with trace_lock:
            last_trace = []
        last_confidence = 0
        last_metrics = {"agents": 2, "tools": 0, "checkpoints": state.checkpoints, "recoveries": 0, "routes": 0}
        for _ in range(self.max_rounds):
            route = self._route(state)
            if route == "finish":
                self.checkpoints.save(state)
                last_confidence = round(state.confidence * 100)
                return state.report
            if route in state.route_history:
                state.failed["deadlock"] = "Repeated route detected; verification forced."
                last_run_telemetry.append("GUARD // loop detected // rerouting to verification")
                route = "verify"
            state.route_history.append(route)
            last_metrics["routes"] += 1
            route_started = time.perf_counter()
            self._checkpoint(state)
            if route == "collect":
                self._collect_parallel(state)
            elif route == "verify":
                self._verify_and_replan(state)
            else:
                self._analyze(state)
            _record_trace("Orchestrator", route.upper(), route_started, "SUCCESS", "Conditional route completed", len(route) * 8)
        raise RuntimeError("Bounded planning budget exhausted before completion")

    def _route(self, state):
        if not state.evidence and state.budget > 0:
            return "collect"
        if (state.confidence < 0.7 or state.conflicts) and state.budget > 0:
            return "verify"
        if not state.report:
            return "analyze"
        return "finish"

    def _collect_parallel(self, state):
        pending = [task for task in state.plan if task not in state.completed][:min(self.max_parallel, state.budget)]
        last_run_telemetry.append(f"PLAN // parallel branches dispatched: {', '.join(pending)}")
        with ThreadPoolExecutor(max_workers=len(pending) or 1) as pool:
            futures = {pool.submit(self._run_with_fallback, task, state): task for task in pending}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    state.evidence.extend(self._coerce(task, future.result()))
                    state.completed.append(task)
                    last_run_telemetry.append(f"TOOL // {task} // completed")
                except Exception as exc:
                    state.failed[task] = str(exc)
                    last_run_telemetry.append(f"TOOL // {task} // failed: {type(exc).__name__}")
                state.budget -= 1
                last_metrics["tools"] += 1
        self._resolve_conflicts(state)

    def _run_with_fallback(self, task, state):
        started = time.perf_counter()
        try:
            result = self.executor(task, asdict(state))
            _record_trace("Data Scout", task, started, "SUCCESS", "Primary tool call", 180)
            return result
        except Exception as primary:
            _record_trace("Data Scout", task, started, "FAILED", f"{type(primary).__name__}: {primary}", 180)
            fallback = self.fallbacks.get(task, "research")
            last_metrics["recoveries"] += 1
            last_run_telemetry.append(f"RECOVERY // {task} failed // fallback: {fallback}")
            fallback_started = time.perf_counter()
            try:
                result = self.executor(fallback, asdict(state))
                _record_trace("Recovery Controller", fallback, fallback_started, "FALLBACK", f"Recovered from {task}", 140)
                return self._tag_fallback(result, task, fallback)
            except Exception as secondary:
                _record_trace("Recovery Controller", fallback, fallback_started, "FAILED", f"{type(secondary).__name__}: {secondary}", 140)
                raise RuntimeError(f"{task}: {primary}; fallback: {secondary}")

    @staticmethod
    def _tag_fallback(result, original_task, fallback_task):
        # Preserve whatever claim/content/confidence the fallback tool actually
        # returned instead of discarding it into a stringified dict. Only the
        # provenance (`source`) is rewritten so downstream conflict-grouping in
        # _resolve_conflicts (which groups by claim text) still works correctly
        # for fallback-sourced evidence.
        tag = f"fallback:{fallback_task}(from {original_task})"
        if isinstance(result, dict):
            tagged = dict(result)
            tagged["source"] = tag
            return tagged
        if isinstance(result, list):
            return [{"claim": str(item), "source": tag, "content": str(item)} for item in result]
        return {"claim": str(result), "source": tag, "content": str(result)}

    @staticmethod
    def _coerce(task, result):
        if isinstance(result, dict):
            return [Evidence(str(result.get("claim", result.get("content", ""))), str(result.get("source", task)), str(result.get("content", result)), float(result.get("confidence", 0.5)))]
        if isinstance(result, list):
            return [Evidence(str(item), task, str(item)) for item in result]
        return [Evidence(str(result), task, str(result))]

    def _resolve_conflicts(self, state):
        # Reset every item to its original confidence before re-evaluating
        # conflicts. Without this, repeated calls (e.g. once per verify round)
        # would keep multiplying an already-penalized value by 0.5 again,
        # driving confidence toward zero regardless of new verification
        # evidence. Resetting first makes the penalty a function of current
        # conflict state only, so it converges instead of decaying forever.
        for item in state.evidence:
            item.confidence = item.base_confidence

        groups = {}
        for item in state.evidence:
            groups.setdefault(item.claim.lower().strip(), []).append(item)
        state.conflicts = []
        for claim, items in groups.items():
            if len(items) > 1 and any(word in item.content.lower() for item in items for word in ("false", "contradict")):
                state.conflicts.append(claim)
                for item in items:
                    item.confidence = item.base_confidence * 0.5
        state.confidence = min(1.0, sum(item.confidence for item in state.evidence) / max(len(state.evidence), 1))
        if state.conflicts:
            last_run_telemetry.append(f"EVALUATION // {len(state.conflicts)} conflicting claim(s) // verification required")

    def _verify_and_replan(self, state):
        state.hypotheses = [item.claim for item in state.evidence if item.confidence < 0.7]
        last_run_telemetry.append(f"VERIFY // {len(state.hypotheses)} hypothesis/hypotheses selected")
        if state.budget > 0:
            verify_started = time.perf_counter()
            result = self.executor("verify", {**asdict(state), "hypotheses": state.hypotheses})
            _record_trace("Evidence Verifier", "verify", verify_started, "SUCCESS", "Hypothesis verification", 160)
            state.evidence.extend(self._coerce("verify", result))
            state.completed.append("verify")
            state.budget -= 1
            self._resolve_conflicts(state)
        state.confidence = min(1.0, state.confidence + 0.1)
        last_run_telemetry.append("REPLAN // verification complete // plan confidence updated")

    def _analyze(self, state):
        analysis_started = time.perf_counter()
        result = self.executor("analysis", {**asdict(state), "evidence": [asdict(item) for item in state.evidence]})
        state.report = str(result.raw) if hasattr(result, "raw") else str(result)
        _record_trace("Senior Analyst", "analysis", analysis_started, "SUCCESS", "Report synthesis", 260)
        # Confidence must reflect what the evidence actually supports, not
        # merely whether evidence objects exist. Evidence with real content
        # was previously indistinguishable from empty/placeholder evidence --
        # both got a flat 0.75 floor, which fabricates certainty for
        # incomplete-evidence scenarios instead of surfacing the gap.
        evidence_confidence = (
            sum(item.confidence for item in state.evidence) / len(state.evidence)
            if state.evidence else 0.0
        )
        state.confidence = max(state.confidence, evidence_confidence)
        report_memory = f"Topic: {state.topic}\nCompetitor: {state.competitor}\n\n{state.report}"
        if not is_duplicate_insight(report_memory):
            store_new_insight(
                summary=report_memory,
                source="CrewAI Senior Analyst",
                category="Executive Intelligence Briefing",
                impact_score=max(1, min(10, round(state.confidence * 10))),
            )
        for item in state.evidence:
            evidence_memory = f"Topic: {state.topic}\nCompetitor: {state.competitor}\nClaim: {item.claim}\nSource: {item.source}\nEvidence: {item.content}"
            if item.content and not is_duplicate_insight(evidence_memory):
                store_new_insight(
                    summary=evidence_memory,
                    source=item.source,
                    category="Research Evidence",
                    impact_score=max(1, min(10, round(item.confidence * 10))),
                )
        last_run_telemetry.append("MEMORY // executive briefing stored for follow-up questions")
        last_run_telemetry.append("ANALYST // synthesis complete // report normalized to text")

    def _checkpoint(self, state):
        state.checkpoints += 1
        last_metrics["checkpoints"] = state.checkpoints
        self.checkpoints.save(state)
        last_run_telemetry.append(f"STATE // checkpoint {state.checkpoints} saved")

    @staticmethod
    def _crewai_executor(task_name, state):
        from crewai import Crew, LLM, Process
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing")
        llm = LLM(model=os.getenv("OPENROUTER_MODEL", "openrouter/openai/gpt-4o-mini"), api_key=api_key, base_url="https://openrouter.ai/api/v1")
        scout = create_scout_agent()
        scout.llm = llm
        scout.max_iter = 2
        if task_name == "analysis":
            analyst = create_analyst_agent()
            analyst.llm = llm
            analyst.max_iter = 2
            gather = create_gathering_task(scout, state["topic"], state["competitor"])
            task = create_analysis_task(analyst, gather, state["topic"])
            crew = Crew(agents=[scout, analyst], tasks=[task], process=Process.sequential, memory=True, max_rpm=15)
        else:
            task = create_gathering_task(scout, state["topic"], state["competitor"])
            crew = Crew(agents=[scout], tasks=[task], process=Process.sequential, memory=True, max_rpm=15)
        return crew.kickoff()


def run_tracker(topic: str, competitor: str):
    return DynamicCrewOrchestrator().run(topic, competitor)