"""Dynamic CrewAI orchestration for competitor research."""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

Executor = Callable[[str, Dict[str, Any]], Any]


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
	"""File-backed checkpoints; injectable for tests and other storage backends."""

	def __init__(self, directory: Optional[Path] = None):
		self.directory = directory or Path(os.getenv("CHECKPOINT_DIR", "checkpoints"))

	def save(self, state: ResearchState) -> None:
		self.directory.mkdir(parents=True, exist_ok=True)
		payload = asdict(state)
		payload["saved_at"] = datetime.now(timezone.utc).isoformat()
		(self.directory / f"{self._key(state.topic, state.competitor)}.json").write_text(
			json.dumps(payload, indent=2), encoding="utf-8"
		)

	def load(self, topic: str, competitor: str) -> Optional[ResearchState]:
		target = self.directory / f"{self._key(topic, competitor)}.json"
		if not target.exists():
			return None
		payload = json.loads(target.read_text(encoding="utf-8"))
		payload.pop("saved_at", None)
		payload["evidence"] = [Evidence(**item) for item in payload.get("evidence", [])]
		return ResearchState(**payload)

	@staticmethod
	def _key(topic: str, competitor: str) -> str:
		value = f"{topic.strip().lower()}::{competitor.strip().lower()}".encode()
		return hashlib.sha256(value).hexdigest()[:20]


class DynamicCrewOrchestrator:
	"""Bounded, stateful, self-evaluating CrewAI control loop."""

	FALLBACKS = {"web": "research", "research": "patent", "patent": "web"}

	def __init__(self, executor: Optional[Executor] = None, checkpoint_store: Optional[JsonCheckpointStore] = None, max_rounds: int = 5, max_parallel: int = 3):
		self.executor = executor or self._crewai_executor
		self.checkpoints = checkpoint_store or JsonCheckpointStore()
		self.max_rounds = max_rounds
		self.max_parallel = max_parallel

	def run(self, topic: str, competitor: str, budget: int = 6) -> str:
		state = self.checkpoints.load(topic, competitor) or ResearchState(topic, competitor, budget)
		for _ in range(self.max_rounds):
			route = self._route(state)
			if route == "finish":
				self.checkpoints.save(state)
				return state.report
			if route in state.route_history:
				state.failed["deadlock"] = "Repeated route detected; forcing verification."
				route = "verify"
			state.route_history.append(route)
			self._checkpoint(state)
			if route == "collect":
				self._collect_parallel(state)
			elif route == "verify":
				self._verify_and_replan(state)
			else:
				self._analyze(state)
		raise RuntimeError("Agent loop exhausted its bounded planning budget")

	def _route(self, state: ResearchState) -> str:
		if not state.evidence and state.budget > 0:
			return "collect"
		if state.confidence < 0.65 and state.budget > 0:
			return "verify"
		if not state.report:
			return "analyze"
		return "finish"

	def _collect_parallel(self, state: ResearchState) -> None:
		pending = [task for task in state.plan if task not in state.completed][:min(self.max_parallel, state.budget)]
		with ThreadPoolExecutor(max_workers=len(pending) or 1) as pool:
			futures = {pool.submit(self._run_with_fallback, task, state): task for task in pending}
			for future in as_completed(futures):
				task = futures[future]
				try:
					state.evidence.extend(self._coerce_evidence(task, future.result()))
					state.completed.append(task)
				except Exception as exc:
					state.failed[task] = str(exc)
				state.budget -= 1
		self._resolve_conflicts(state)

	def _run_with_fallback(self, task: str, state: ResearchState) -> Any:
		try:
			return self.executor(task, asdict(state))
		except Exception as primary_error:
			fallback = self.FALLBACKS[task]
			try:
				return {"source": f"fallback:{fallback}", "content": str(self.executor(fallback, asdict(state)))}
			except Exception as fallback_error:
				raise RuntimeError(f"{task} failed: {primary_error}; fallback failed: {fallback_error}")

	@staticmethod
	def _coerce_evidence(task: str, result: Any) -> Iterable[Evidence]:
		if isinstance(result, list):
			return [Evidence(str(item), task, str(item)) for item in result]
		if isinstance(result, dict):
			return [Evidence(str(result.get("claim", result.get("content", ""))), str(result.get("source", task)), str(result.get("content", result)), float(result.get("confidence", 0.5)))]
		return [Evidence(str(result), task, str(result))]

	def _resolve_conflicts(self, state: ResearchState) -> None:
		grouped: Dict[str, List[Evidence]] = {}
		for item in state.evidence:
			grouped.setdefault(item.claim.lower().strip(), []).append(item)
		state.conflicts = []
		for claim, items in grouped.items():
			if len(items) > 1 and any("false" in item.content.lower() or "contradict" in item.content.lower() for item in items):
				state.conflicts.append(claim)
				for item in items:
					item.confidence *= 0.5
		state.confidence = min(1.0, sum(item.confidence for item in state.evidence) / max(len(state.evidence), 1))

	def _verify_and_replan(self, state: ResearchState) -> None:
		state.hypotheses = [item.claim for item in state.evidence if item.confidence < 0.65]
		if state.budget > 0:
			try:
				result = self.executor("verify", {"hypotheses": state.hypotheses, "conflicts": state.conflicts, **asdict(state)})
				state.evidence.extend(self._coerce_evidence("verify", result))
				state.completed.append("verify")
				state.budget -= 1
				self._resolve_conflicts(state)
			except Exception as exc:
				state.failed["verify"] = str(exc)
				state.budget -= 1
		if state.budget > 0 and "research" not in state.completed:
			state.plan.append("research")
		state.confidence = min(1.0, state.confidence + 0.1)

	def _analyze(self, state: ResearchState) -> None:
		payload = {"topic": state.topic, "competitor": state.competitor, "evidence": [asdict(item) for item in state.evidence], "conflicts": state.conflicts}
		state.report = str(self.executor("analysis", payload))
		state.confidence = max(state.confidence, 0.7 if state.evidence else 0.0)

	def _checkpoint(self, state: ResearchState) -> None:
		state.checkpoints += 1
		self.checkpoints.save(state)

	@staticmethod
	def _crewai_executor(task_name: str, state: Dict[str, Any]) -> Any:
		from crewai import Crew, LLM, Process
		from agents.analyst_agent import create_analyst_agent
		from agents.scout_agent import create_scout_agent
		from tasks.analysis_tasks import create_analysis_task
		from tasks.gathering_tasks import create_gathering_task

		api_key = os.getenv("GEMINI_API_KEY")
		if not api_key:
			raise ValueError("GEMINI_API_KEY is missing")
		llm = LLM(model="gemini/gemini-3.6-flash", api_key=api_key)
		scout = create_scout_agent()
		scout.llm = llm
		if task_name == "analysis":
			analyst = create_analyst_agent()
			analyst.llm = llm
			gathering = create_gathering_task(scout, state["topic"], state["competitor"])
			task = create_analysis_task(analyst, gathering, state["topic"])
			crew = Crew(agents=[scout, analyst], tasks=[task], process=Process.sequential, memory=True, max_rpm=15)
		else:
			task = create_gathering_task(scout, state["topic"], state["competitor"])
			crew = Crew(agents=[scout], tasks=[task], process=Process.sequential, memory=True, max_rpm=15)
		return crew.kickoff()


def run_tracker(topic: str, competitor: str) -> str:
	return DynamicCrewOrchestrator().run(topic, competitor)
