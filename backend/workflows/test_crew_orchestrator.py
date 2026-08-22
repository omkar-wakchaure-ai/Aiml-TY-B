import tempfile
import unittest
from pathlib import Path

from .crew_orchestrator import DynamicCrewOrchestrator, JsonCheckpointStore


class AdversarialExecutor:
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


class DynamicOrchestratorTests(unittest.TestCase):
    def test_adversarial_recovery_conflict_checkpoint_and_replan(self):
        with tempfile.TemporaryDirectory() as directory:
            executor = AdversarialExecutor()
            orchestrator = DynamicCrewOrchestrator(
                executor=executor,
                checkpoint_store=JsonCheckpointStore(Path(directory)),
                max_rounds=5,
            )
            report = orchestrator.run("solid state battery", "Competitor X", budget=5)

            self.assertIn("Final report", report)
            self.assertIn("research", executor.calls)
            self.assertIn("patent", executor.calls)
            self.assertIn("analysis", executor.calls)
            self.assertTrue(list(Path(directory).glob("*.json")))


if __name__ == "__main__":
    unittest.main()
