"""
Unit test suite for Capybala AgentHealer and Supervisor clients.
"""

import unittest
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.healer import AgentHealer
from capybala.models.supervisor import MockSupervisorClient


class TestCapybalaHealer(unittest.TestCase):
    def setUp(self):
        self.healer = AgentHealer()

    def test_heuristic_import_error_pivot(self):
        rx = self.healer.prescribe(
            deadlock_pattern="semantic_traceback",
            failing_action="pytest tests/test_api.py",
            error_signature="ImportError: cannot import name 'FastAPI'",
            task_prompt="Fix broken import in backend API"
        )
        self.assertEqual(rx.mode_used, "heuristic")
        self.assertIn("sys.path", rx.recommended_pivot.lower())
        self.assertIn("[🦫 CAPYBALA DOCTOR INTERVENTION]", rx.injected_message["content"])

    def test_heuristic_assertion_error_pivot(self):
        rx = self.healer.prescribe(
            deadlock_pattern="direct_repetition",
            failing_action="pytest tests/",
            error_signature="AssertionError: assert 404 == 200",
            task_prompt="Fix status code response"
        )
        self.assertIn("test assertions failed", rx.recommended_pivot.lower())

    def test_heuristic_oscillation_pivot(self):
        rx = self.healer.prescribe(
            deadlock_pattern="oscillation",
            failing_action="git checkout -- file.py",
            error_signature="FAILED",
            task_prompt="Fix flaky test"
        )
        self.assertIn("third, completely new hypothesis", rx.recommended_pivot.lower())

    def test_supervisor_mock_integration(self):
        mock_client = MockSupervisorClient(return_text="Inspect database migration 0004.")
        llm_healer = AgentHealer(supervisor_client=mock_client)
        rx = llm_healer.prescribe(
            deadlock_pattern="direct_repetition",
            failing_action="alembic upgrade head",
            error_signature="OperationalError",
            use_supervisor_llm=True
        )
        self.assertEqual(rx.mode_used, "supervisor_llm")
        self.assertEqual(rx.recommended_pivot, "Inspect database migration 0004.")
        self.assertIn("Inspect database migration 0004.", rx.injected_message["content"])

    def test_full_pipeline_end_to_end(self):
        detector = DeadlockDetector(repetition_threshold=3)
        pruner = ContextPruner()
        healer = AgentHealer()

        messages = [
            {"role": "system", "content": "You are an autonomous AI coding agent."},
            {"role": "user", "content": "Fix issue #102 in django-rest."}
        ]

        action = "python manage.py test"
        err = "Traceback (most recent call last):\nImportError: No module named 'rest_framework'"

        # Simulate 3 consecutive failures
        deadlock_event = None
        for _ in range(3):
            messages.append({"role": "assistant", "content": action})
            messages.append({"role": "tool", "content": err})
            deadlock_event = detector.check(action, err)

        self.assertTrue(deadlock_event.is_deadlock)

        # Step 1: Prune toxic history
        prune_res = pruner.prune(messages, deadlock_reason=deadlock_event.details, cycle_length=4)
        self.assertLess(len(prune_res.pruned_messages), len(messages))

        # Step 2: Inject Doctor Prescription
        rx = healer.prescribe(
            deadlock_pattern=deadlock_event.pattern_type,
            failing_action=action,
            error_signature=err
        )
        rescued_messages = prune_res.pruned_messages + [rx.injected_message]

        # Verify rescued messages structure
        self.assertEqual(rescued_messages[0]["role"], "system")
        self.assertEqual(rescued_messages[1]["role"], "user")
        self.assertIn("CAPYBALA DOCTOR INTERVENTION", rescued_messages[-1]["content"])


if __name__ == "__main__":
    unittest.main()

