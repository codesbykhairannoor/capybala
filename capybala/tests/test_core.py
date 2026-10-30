"""
Unit test suite for capybala core engine:
- DeadlockDetector (repetition, oscillation, semantic traceback)
- ContextPruner (surgical cycle collapsing, prompt protection)
"""

import unittest
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner


class TestCapybalaDetector(unittest.TestCase):
    def setUp(self):
        self.detector = DeadlockDetector(repetition_threshold=3, oscillation_threshold=2)

    def test_normal_healthy_progression(self):
        actions = [
            "ls -la",
            "cat pyproject.toml",
            "git status",
            "pytest tests/test_auth.py"
        ]
        for act in actions:
            event = self.detector.check(act, "Files listed successfully.")
            self.assertFalse(event.is_deadlock)

    def test_direct_repetition(self):
        # 1st time
        ev1 = self.detector.check("pytest tests/", "FAILED: 1 error")
        self.assertFalse(ev1.is_deadlock)

        # 2nd time
        ev2 = self.detector.check("pytest tests/", "FAILED: 1 error")
        self.assertFalse(ev2.is_deadlock)

        # 3rd time -> Deadlock!
        ev3 = self.detector.check("pytest tests/", "FAILED: 1 error")
        self.assertTrue(ev3.is_deadlock)
        self.assertEqual(ev3.pattern_type, "direct_repetition")
        self.assertEqual(ev3.repetition_count, 3)

    def test_oscillation_2step(self):
        # Cycle: edit -> test -> revert -> test -> edit -> test -> revert -> test
        self.detector.check("git checkout -- foo.py", "reverted")
        self.detector.check("pytest tests/", "FAILED")
        self.detector.check("git checkout -- foo.py", "reverted")
        ev = self.detector.check("pytest tests/", "FAILED")

        self.assertTrue(ev.is_deadlock)
        self.assertEqual(ev.pattern_type, "oscillation")

    def test_semantic_traceback_with_varying_commands(self):
        # Commands vary slightly, but the exact same fatal Exception repeats 3 times
        tb = (
            "Traceback (most recent call last):\n"
            "  File '/tmp/tmp987abc/app.py', line 45, in <module>\n"
            "ImportError: cannot import name 'FastAPI' from 'fastapi'"
        )

        self.detector.check("python -m app", tb)
        self.detector.check("python app.py --debug", tb)
        ev = self.detector.check("uvicorn app:app", tb)

        self.assertTrue(ev.is_deadlock)
        self.assertEqual(ev.pattern_type, "semantic_traceback")


class TestCapybalaPruner(unittest.TestCase):
    def setUp(self):
        self.pruner = ContextPruner()

    def test_protection_of_system_and_user_prompts(self):
        messages = [
            {"role": "system", "content": "You are a software engineer agent."},
            {"role": "user", "content": "Fix the bug in repo/issue-404."},
            {"role": "assistant", "content": "Let me run pytest."},
            {"role": "tool", "content": "FAILED Traceback... (1,000 bytes error log)" * 5},
            {"role": "assistant", "content": "Let me run pytest again."},
            {"role": "tool", "content": "FAILED Traceback... (1,000 bytes error log)" * 5},
            {"role": "assistant", "content": "Let me run pytest one more time."},
            {"role": "tool", "content": "FAILED Traceback... latest state"}
        ]

        result = self.pruner.prune(messages, deadlock_reason="Repeated pytest failure", cycle_length=4)

        # 1. System prompt preserved at index 0
        self.assertEqual(result.pruned_messages[0]["role"], "system")
        self.assertEqual(result.pruned_messages[0]["content"], "You are a software engineer agent.")

        # 2. User initial task preserved at index 1
        self.assertEqual(result.pruned_messages[1]["role"], "user")
        self.assertEqual(result.pruned_messages[1]["content"], "Fix the bug in repo/issue-404.")

        # 3. Tombstone inserted
        tombstone = [m for m in result.pruned_messages if "CAPYBALA PRUNING" in m.get("content", "")]
        self.assertEqual(len(tombstone), 1)

        # 4. Token savings verified
        self.assertGreater(result.tokens_saved_estimate, 100)
        self.assertLess(len(result.pruned_messages), len(messages))


if __name__ == "__main__":
    unittest.main()

