import unittest
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.healer import AgentHealer
from capybala.api import heal


class TestV060EmpiricalHardening(unittest.TestCase):
    """
    Unit tests for Capybala v0.6.0 empirical features:
    - Exploration Thrashing / Wandering Guard
    - Adaptive Syntax Refinement Grace Period
    - Dead Negative Search Pruning
    - Tailored Strategic Directives for Exploration Deadlocks
    """

    def test_exploration_thrashing_detection(self):
        """Verifies that 15 consecutive read-only search operations trip exploration thrashing."""
        detector = DeadlockDetector(max_exploration_depth=10)

        # 9 consecutive read-only actions
        for i in range(9):
            res = detector.check(f"grep 'pattern_{i}' src/module.py", f"File output line {i}")
            self.assertFalse(res.is_deadlock, f"Turn {i} should not be flagged yet")

        # 10th read-only action hits max_exploration_depth=10
        res = detector.check("find_file 'config.yaml' src", "File not found")
        self.assertTrue(res.is_deadlock)
        self.assertEqual(res.pattern_type, "exploration_thrashing")
        self.assertEqual(res.repetition_count, 10)
        self.assertIn("Exploration thrashing detected", res.details)

    def test_mutating_action_resets_exploration_counter(self):
        """Verifies that an edit, test execution, or file write resets the exploration counter."""
        detector = DeadlockDetector(max_exploration_depth=5)

        # 4 read-only actions
        for i in range(4):
            detector.check(f"cat file_{i}.py", "content")

        # 5th action is mutating (code edit)
        res = detector.check("edit 10:20\ndef new_func(): pass", "Edit successful")
        self.assertFalse(res.is_deadlock)
        self.assertEqual(detector.consecutive_exploration_turns, 0)

        # Next 4 read-only actions should not trigger
        for i in range(4):
            res = detector.check(f"cat other_{i}.py", "content")
            self.assertFalse(res.is_deadlock)

    def test_active_code_refinement_syntax_grace_period(self):
        """
        Verifies that when an agent is actively refining code payloads after a syntax error,
        it receives an adaptive grace period (repetition_threshold + 1) to avoid premature termination.
        """
        detector = DeadlockDetector(repetition_threshold=3)

        # Turn 1: Initial edit attempt with syntax error
        res1 = detector.check(
            "edit 1:5\ndef foo():\n  x = 1",
            "Your proposed edit has introduced new syntax error(s). Please fix and retry."
        )
        self.assertFalse(res1.is_deadlock)

        # Turn 2: Second edit attempt with modified payload (refinement)
        res2 = detector.check(
            "edit 1:5\ndef foo():\n    x = 1\n    return x",
            "Your proposed edit has introduced new syntax error(s). Please fix and retry."
        )
        self.assertFalse(res2.is_deadlock)

        # Turn 3: Third edit attempt with modified payload (still actively refining)
        res3 = detector.check(
            "edit 1:6\ndef foo():\n    x = 1\n    return (x + 1)",
            "Your proposed edit has introduced new syntax error(s). Please fix and retry."
        )
        # Because the agent is actively modifying the code, Turn 3 is granted grace period!
        self.assertFalse(res3.is_deadlock, "Turn 3 should be granted grace period for active syntax refinement")

        # Turn 4: Fourth edit attempt with another syntax failure triggers threshold of 4
        res4 = detector.check(
            "edit 1:6\ndef foo():\n    x = 1\n    return (x + 2)",
            "Your proposed edit has introduced new syntax error(s). Please fix and retry."
        )
        self.assertTrue(res4.is_deadlock, "Turn 4 should trip after exceeding adaptive grace period")
        self.assertEqual(res4.pattern_type, "fuzzy_repetition")

    def test_prune_dead_searches(self):
        """Verifies that ContextPruner compresses ancient negative tool searches."""
        pruner = ContextPruner()

        messages = [
            {"role": "system", "content": "You are a software engineer."},
            {"role": "user", "content": "Fix the bug in the repo."},
            {"role": "assistant", "content": "Let me search for the class."},
            # Ancient dead search 1
            {"role": "tool", "content": "No matches found for 'class OldOrchestrator' in /repo/src\n" * 10},
            {"role": "assistant", "content": "Let me check directory."},
            # Ancient dead search 2
            {"role": "user", "content": "Directory src/legacy not found in current workspace\n" * 10},
            {"role": "assistant", "content": "Found the right file, let's open it."},
            # Recent messages (should not be touched)
            {"role": "tool", "content": "Found 5 matches for 'class ActiveOrchestrator' in /repo/active.py"},
            {"role": "assistant", "content": "Editing active.py"},
            {"role": "user", "content": "Edit applied."},
        ]

        result = pruner.prune_dead_searches(messages, max_age_turns=4)
        pruned = result.pruned_messages

        self.assertEqual(len(pruned), len(messages))
        self.assertIn("[Search Result: 0 matches found", pruned[3]["content"])
        self.assertIn("[Search Result: 0 matches found", pruned[5]["content"])
        self.assertIn("Found 5 matches for 'class ActiveOrchestrator'", pruned[7]["content"])
        self.assertGreater(result.characters_saved, 100)

    def test_exploration_thrashing_healer_guidance(self):
        """Verifies that AgentHealer generates tailored strategic guidance for exploration thrashing."""
        healer = AgentHealer()
        prescription = healer._generate_heuristic_pivot(
            error_signature="",
            pattern_type="exploration_thrashing",
            failing_action="search 'class PlainOrchestrator'",
            escalation_level=1
        )
        self.assertIn("Exploration thrashing detected", prescription)
        self.assertIn("STOP inspecting files", prescription)
        self.assertIn("Formulate a concrete code modification hypothesis", prescription)


if __name__ == "__main__":
    unittest.main()
