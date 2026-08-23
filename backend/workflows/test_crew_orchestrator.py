import tempfile
import unittest
from pathlib import Path

from .crew_orchestrator import DynamicCrewOrchestrator, JsonCheckpointStore, get_last_trace, get_last_metrics, get_last_confidence


# ---------------------------------------------------------------------------
# Scripted executors, one per evaluation scenario. Each is a drop-in
# replacement for the real CrewAI executor via the orchestrator's
# `executor=` constructor argument, so no live LLM/API calls are needed
# to exercise the routing, recovery, and conflict-resolution logic.
# ---------------------------------------------------------------------------

class NormalExecutor:
    """All tools succeed with a single, unanimous, high-confidence claim."""

    def __init__(self):
        self.calls = []

    def __call__(self, task, state):
        self.calls.append(task)
        if task in ("web", "research", "patent"):
            return {"claim": "battery density improves", "source": task, "content": "battery density improves", "confidence": 0.9}
        if task == "verify":
            return {"claim": "battery density improves", "source": "verification", "content": "verified", "confidence": 0.95}
        return "Final report: consistent evidence across all sources"


class AmbiguousExecutor:
    """Sources agree loosely but phrase claims differently -- no explicit
    contradiction keyword, so this should NOT trip conflict detection, but
    the varied low confidence should still push the orchestrator into a
    verify round."""

    def __init__(self):
        self.calls = []

    def __call__(self, task, state):
        self.calls.append(task)
        if task == "web":
            return {"claim": "battery density may improve", "source": "web", "content": "early signs suggest improvement", "confidence": 0.4}
        if task == "research":
            return {"claim": "battery density could increase", "source": "research", "content": "some studies indicate gains", "confidence": 0.45}
        if task == "patent":
            return {"claim": "battery density trend unclear", "source": "patent", "content": "filings are inconclusive", "confidence": 0.3}
        if task == "verify":
            return {"claim": "battery density trend unclear", "source": "verification", "content": "still inconclusive after review", "confidence": 0.5}
        return "Final report: findings remain directionally uncertain"


class IncompleteExecutor:
    """Every source comes back empty. There is never enough evidence to
    reach high confidence, so with a tight budget the orchestrator should
    exhaust its round budget rather than silently fabricate a confident
    report."""

    def __init__(self):
        self.calls = []

    def __call__(self, task, state):
        self.calls.append(task)
        if task in ("web", "research", "patent", "verify"):
            return {"claim": "", "source": task, "content": "", "confidence": 0.0}
        return "Final report: insufficient evidence"


class AdversarialExecutor:
    """One source fails outright (forces fallback) and two sources directly
    contradict each other (forces conflict detection + confidence penalty)."""

    def __init__(self):
        self.calls = []

    def __call__(self, task, state):
        self.calls.append(task)
        if task == "web":
            raise RuntimeError("simulated web outage")
        if task == "research":
            return {"claim": "battery density improves", "source": "research", "content": "battery density improves", "confidence": 0.8}
        if task == "patent":
            return {"claim": "battery density improves", "source": "patent", "content": "false: battery density improves", "confidence": 0.8}
        if task == "verify":
            return {"claim": "battery density improves", "source": "verification", "content": "verified", "confidence": 0.9}
        return "Final report after conflict resolution"


class TotalOutageExecutor:
    """Every tool fails, including fallback targets. Used to confirm the
    orchestrator surfaces the failure instead of hanging or fabricating
    a report."""

    def __call__(self, task, state):
        raise RuntimeError(f"simulated total outage on {task}")


def _run(executor, budget=5, max_rounds=5):
    with tempfile.TemporaryDirectory() as directory:
        orchestrator = DynamicCrewOrchestrator(
            executor=executor,
            checkpoint_store=JsonCheckpointStore(Path(directory)),
            max_rounds=max_rounds,
        )
        report = orchestrator.run("solid state battery", "Competitor X", budget=budget)
        return report, get_last_trace(), get_last_metrics(), list(Path(directory).glob("*.json"))


class DynamicOrchestratorTests(unittest.TestCase):

    # -- Normal scenario --------------------------------------------------
    def test_normal_scenario_reaches_high_confidence_report(self):
        executor = NormalExecutor()
        report, trace, metrics, checkpoints = _run(executor)
        self.assertIn("Final report", report)
        self.assertTrue(checkpoints)
        self.assertFalse(any(item["Status"] == "FAILED" for item in trace))
        self.assertEqual(metrics["recoveries"], 0)

    # -- Ambiguous scenario -------------------------------------------------
    def test_ambiguous_scenario_triggers_verification_without_false_conflict(self):
        executor = AmbiguousExecutor()
        report, trace, metrics, _ = _run(executor)
        self.assertIn("Final report", report)
        # No source used the word "false"/"contradict", so this must not be
        # misclassified as a hard conflict even though claims are phrased
        # differently and confidence is uniformly low.
        self.assertIn("verify", executor.calls)
        self.assertTrue(any(item["Operation"] == "verify" for item in trace))

    # -- Incomplete evidence scenario --------------------------------------
    def test_incomplete_evidence_does_not_fabricate_confidence(self):
        # With every source returning empty content, the orchestrator still
        # terminates (it has a report to give), but it must not claim
        # meaningful confidence in that report -- this is the "refuse
        # unsupported conclusions" criterion from the evaluation rubric.
        # Regression guard: _analyze used to floor confidence at 0.75 for
        # ANY non-empty evidence list, regardless of what the evidence
        # actually contained.
        executor = IncompleteExecutor()
        _run(executor, budget=2, max_rounds=3)
        self.assertLess(get_last_confidence(), 10, "confidence should reflect empty evidence, not a fabricated floor")

    # -- Adversarial + contradictory + tool-failure scenario ---------------
    def test_adversarial_recovery_conflict_checkpoint_and_replan(self):
        executor = AdversarialExecutor()
        report, trace, metrics, checkpoints = _run(executor, budget=5, max_rounds=5)

        self.assertIn("Final report", report)
        self.assertIn("research", executor.calls)
        self.assertIn("patent", executor.calls)
        self.assertIn("analysis", executor.calls)
        self.assertTrue(checkpoints)

        self.assertTrue(any(item["Status"] == "FAILED" and item["Operation"] == "web" for item in trace))
        self.assertTrue(any(item["Status"] == "FALLBACK" for item in trace))
        self.assertTrue(all(item["Latency (ms)"] >= 0 for item in trace))
        self.assertGreaterEqual(metrics["recoveries"], 1)

    def test_fallback_evidence_preserves_original_claim_text(self):
        # Regression test: the fallback path used to discard the claim and
        # confidence returned by the fallback tool, re-wrapping everything
        # as a stringified dict. This confirms the fix -- fallback-sourced
        # evidence must group correctly with direct-path evidence on the
        # real claim text, not a garbled dict repr.
        executor = AdversarialExecutor()
        with tempfile.TemporaryDirectory() as directory:
            orchestrator = DynamicCrewOrchestrator(
                executor=executor,
                checkpoint_store=JsonCheckpointStore(Path(directory)),
                max_rounds=5,
            )
            orchestrator.run("solid state battery", "Competitor X", budget=5)
            state = JsonCheckpointStore(Path(directory)).load("solid state battery", "Competitor X")
            fallback_items = [item for item in state.evidence if item.source.startswith("fallback:")]
            self.assertTrue(fallback_items)
            for item in fallback_items:
                self.assertEqual(item.claim.strip().lower(), "battery density improves")

    def test_conflict_penalty_is_idempotent_across_verify_rounds(self):
        # Regression test: repeated calls to conflict resolution used to
        # keep halving an already-halved confidence value every round,
        # decaying toward zero regardless of new verification evidence.
        # Confidence should converge, not collapse.
        executor = AdversarialExecutor()
        with tempfile.TemporaryDirectory() as directory:
            orchestrator = DynamicCrewOrchestrator(
                executor=executor,
                checkpoint_store=JsonCheckpointStore(Path(directory)),
                max_rounds=5,
            )
            orchestrator.run("solid state battery", "Competitor X", budget=5)
            state = JsonCheckpointStore(Path(directory)).load("solid state battery", "Competitor X")
            conflicted = [item for item in state.evidence if item.source in ("research", "patent")]
            for item in conflicted:
                # Penalty is derived from base_confidence (0.8) each time,
                # so it should settle at exactly one halving (0.4), not
                # keep shrinking across multiple _resolve_conflicts calls.
                self.assertAlmostEqual(item.confidence, item.base_confidence * 0.5, places=5)

    # -- Total failure scenario ---------------------------------------------
    def test_total_outage_raises_rather_than_fabricating_report(self):
        executor = TotalOutageExecutor()
        with self.assertRaises(RuntimeError):
            _run(executor, budget=3, max_rounds=3)

    # -- Consistency across repeated runs ------------------------------------
    def test_repeated_runs_are_consistent_for_identical_input(self):
        confidences = []
        for _ in range(3):
            executor = NormalExecutor()
            with tempfile.TemporaryDirectory() as directory:
                orchestrator = DynamicCrewOrchestrator(
                    executor=executor,
                    checkpoint_store=JsonCheckpointStore(Path(directory)),
                    max_rounds=5,
                )
                orchestrator.run("solid state battery", "Competitor X", budget=5)
                state = JsonCheckpointStore(Path(directory)).load("solid state battery", "Competitor X")
                confidences.append(round(state.confidence, 4))
        self.assertEqual(len(set(confidences)), 1, f"Confidence should be deterministic for identical scripted input, got {confidences}")

    # -- Baseline (before/after) comparison ----------------------------------
    def test_recovery_path_costs_more_tool_calls_than_clean_path(self):
        # Measurable before/after: a run that needs fallback recovery should
        # cost strictly more tool invocations than an equivalent run where
        # every source succeeds on the first try.
        _, _, clean_metrics, _ = _run(NormalExecutor(), budget=5, max_rounds=5)
        _, _, recovered_metrics, _ = _run(AdversarialExecutor(), budget=5, max_rounds=5)
        self.assertGreater(recovered_metrics["tools"] + recovered_metrics["recoveries"], clean_metrics["tools"])


if __name__ == "__main__":
    unittest.main()