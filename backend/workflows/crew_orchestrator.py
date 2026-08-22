import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from agents.scout_agent import create_scout_agent
    from agents.analyst_agent import create_analyst_agent
    from tasks.gathering_tasks import create_gathering_task
    from tasks.analysis_tasks import create_analysis_task
except ModuleNotFoundError:
    from ..agents.scout_agent import create_scout_agent
    from ..agents.analyst_agent import create_analyst_agent
    from ..tasks.gathering_tasks import create_gathering_task
    from ..tasks.analysis_tasks import create_analysis_task


@dataclass
class Evidence:
    claim: str
    source: str
    content: str
    confidence: float = 0.5


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


def get_last_run_telemetry():
    return list(last_run_telemetry)


def get_last_confidence():
    return last_confidence


def get_last_metrics():
    return dict(last_metrics)


class DynamicCrewOrchestrator:
    fallbacks = {"web": "research", "research": "patent", "patent": "web"}

    def __init__(self, executor: Optional[Callable] = None, checkpoint_store=None, max_rounds=6, max_parallel=3):
        self.executor = executor or self._crewai_executor
        self.checkpoints = checkpoint_store or JsonCheckpointStore()
        self.max_rounds = max_rounds
        self.max_parallel = max_parallel

    def run(self, topic: str, competitor: str, budget=6):
        global last_run_telemetry, last_confidence, last_metrics
        state = self.checkpoints.load(topic, competitor) or ResearchState(topic, competitor, budget)
        last_run_telemetry = [f"MISSION // {competitor} // {topic}"]
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
            self._checkpoint(state)
            if route == "collect":
                self._collect_parallel(state)
            elif route == "verify":
                self._verify_and_replan(state)
            else:
                self._analyze(state)
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
        try:
            return self.executor(task, asdict(state))
        except Exception as primary:
            fallback = self.fallbacks.get(task, "research")
            last_metrics["recoveries"] += 1
            last_run_telemetry.append(f"RECOVERY // {task} failed // fallback: {fallback}")
            try:
                result = self.executor(fallback, asdict(state))
                return {"source": f"fallback:{fallback}", "content": str(result)}
            except Exception as secondary:
                raise RuntimeError(f"{task}: {primary}; fallback: {secondary}")

    @staticmethod
    def _coerce(task, result):
        if isinstance(result, dict):
            return [Evidence(str(result.get("claim", result.get("content", ""))), str(result.get("source", task)), str(result.get("content", result)), float(result.get("confidence", 0.5)))]
        if isinstance(result, list):
            return [Evidence(str(item), task, str(item)) for item in result]
        return [Evidence(str(result), task, str(result))]

    def _resolve_conflicts(self, state):
        groups = {}
        for item in state.evidence:
            groups.setdefault(item.claim.lower().strip(), []).append(item)
        state.conflicts = []
        for claim, items in groups.items():
            if len(items) > 1 and any(word in item.content.lower() for item in items for word in ("false", "contradict")):
                state.conflicts.append(claim)
                for item in items:
                    item.confidence *= 0.5
        state.confidence = min(1.0, sum(item.confidence for item in state.evidence) / max(len(state.evidence), 1))
        if state.conflicts:
            last_run_telemetry.append(f"EVALUATION // {len(state.conflicts)} conflicting claim(s) // verification required")

    def _verify_and_replan(self, state):
        state.hypotheses = [item.claim for item in state.evidence if item.confidence < 0.7]
        last_run_telemetry.append(f"VERIFY // {len(state.hypotheses)} hypothesis/hypotheses selected")
        if state.budget > 0:
            result = self.executor("verify", {**asdict(state), "hypotheses": state.hypotheses})
            state.evidence.extend(self._coerce("verify", result))
            state.completed.append("verify")
            state.budget -= 1
            self._resolve_conflicts(state)
        state.confidence = min(1.0, state.confidence + 0.1)
        last_run_telemetry.append("REPLAN // verification complete // plan confidence updated")

    def _analyze(self, state):
        result = self.executor("analysis", {**asdict(state), "evidence": [asdict(item) for item in state.evidence]})
        state.report = str(result.raw) if hasattr(result, "raw") else str(result)
        state.confidence = max(state.confidence, 0.75 if state.evidence else 0.0)
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
