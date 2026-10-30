"""
test_v060_ai_arena_hardened.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests synthesized from the Multi-Model Adversarial Arena Debate:
- DeepSeek-V3
- OpenAI GPT-4o-mini
- Anthropic Claude Haiku 4.5
"""

import unittest
from capybala.detector import DeadlockDetector, DeadlockEvent
from capybala.pruner import ContextPruner

class TestV060AIArenaHardened(unittest.TestCase):

    def test_multi_agent_4_cycle_delegation_detected(self):
        """
        DeepSeek-V3 Challenge:
        Simulate a 4-agent delegation cycle: A -> B -> C -> D -> A -> B -> C -> D.
        The detector must catch the 4-agent loop.
        """
        detector = DeadlockDetector(enable_delegation=True)
        actions = [
            "delegate_to(agent='A')",
            "delegate_to(agent='B')",
            "delegate_to(agent='C')",
            "delegate_to(agent='D')",
            "delegate_to(agent='A')",
            "delegate_to(agent='B')",
            "delegate_to(agent='C')",
            "delegate_to(agent='D')",
        ]
        detected = False
        event = None
        for a in actions:
            event = detector.check(a, "")
            if event.is_deadlock:
                detected = True
                break

        self.assertTrue(detected, "4-agent delegation cycle should be detected")
        self.assertEqual(event.pattern_type, "delegation_cycle")
        self.assertIn("4-agent loop", event.details)

    def test_oscillation_4_step_action_loop_detected(self):
        """
        DeepSeek-V3 Challenge:
        Simulate a 4-step action oscillation loop (2 cycles): A -> B -> C -> D -> A -> B -> C -> D.
        The detector must catch the 4-step oscillation.
        """
        detector = DeadlockDetector()
        actions = [
            "python script_a.py",
            "python script_b.py",
            "python script_c.py",
            "python script_d.py",
            "python script_a.py",
            "python script_b.py",
            "python script_c.py",
            "python script_d.py",
        ]
        detected = False
        event = None
        for a in actions:
            event = detector.check(a, "")
            if event.is_deadlock:
                detected = True
                break

        self.assertTrue(detected, "4-step action oscillation should be detected")
        self.assertEqual(event.pattern_type, "oscillation")
        self.assertIn("4-step oscillating action loop", event.details)

    def test_active_code_refinement_with_tool_call_syntax(self):
        """
        DeepSeek-V3 Challenge:
        When an agent calls `edit_file(file='code.py', content='...')` across multiple iterations
        fixing different syntax errors, it must NOT be prematurely killed as a deadlock.
        """
        detector = DeadlockDetector(repetition_threshold=3)
        actions = [
            "edit_file(file='code.py', content='fixed syntax error 1')",
            "edit_file(file='code.py', content='fixed syntax error 2')",
            "edit_file(file='code.py', content='fixed syntax error 3')",
        ]
        observations = [
            "SyntaxError: invalid syntax",
            "SyntaxError: unexpected indent",
            "SyntaxError: missing parentheses",
        ]
        detected = False
        for a, obs in zip(actions, observations):
            event = detector.check(a, obs)
            if event.is_deadlock:
                detected = True
                break

        self.assertFalse(detected, "Active code refinement across different syntax errors must have grace period")

    def test_editor_tool_calls_recognized_as_mutating(self):
        """
        Verify that editor tools (edit_file, str_replace_editor, write_file)
        are recognized as mutating actions, preventing exploration thrashing false alarms.
        """
        detector = DeadlockDetector(max_exploration_depth=5, enable_exploration_guard=True)
        self.assertTrue(detector._is_mutating_or_execution("edit_file(path='foo.py')"))
        self.assertTrue(detector._is_mutating_or_execution("str_replace_editor(path='foo.py')"))
        self.assertTrue(detector._is_mutating_or_execution("write_file(path='foo.py')"))
        self.assertTrue(detector._is_mutating_or_execution("apply_patch(diff='...')"))

        self.assertFalse(detector._is_mutating_or_execution("read_file(path='foo.py')"))
        self.assertFalse(detector._is_mutating_or_execution("view_file(path='foo.py')"))
        self.assertFalse(detector._is_mutating_or_execution("grep_search(query='find')"))

    def test_pruner_non_list_input_resilience(self):
        """
        GPT-4o-mini & DeepSeek Challenge:
        Passing non-list or malformed messages into ContextPruner must never crash.
        """
        pruner = ContextPruner()
        # Integer
        res1 = pruner.rollback_and_reflect(12345, "action", "details")
        self.assertEqual(res1.messages_removed_count, 0)
        self.assertEqual(res1.pruned_messages, [])

        # String
        res2 = pruner.rollback_and_reflect("not a list", "action", "details")
        self.assertEqual(res2.messages_removed_count, 0)
        self.assertEqual(res2.pruned_messages, [])

        # Non-list in prune_dead_searches
        res3 = pruner.prune_dead_searches(9999)
        self.assertEqual(res3.messages_removed_count, 0)
        self.assertEqual(res3.pruned_messages, [])

        # List with malformed non-dict items
        messages = [
            {"role": "user", "content": "hello"},
            None,
            "corrupted_string",
            {"role": "assistant", "content": "hi"},
        ]
        res4 = pruner.rollback_and_reflect(messages, "action", "details")
        self.assertIsNotNone(res4)

    def test_benign_zero_errors_summary_immunity(self):
        """
        GPT-4o-mini Challenge:
        Output containing '0 errors found in the last run.' must not trigger false failure indicators.
        """
        detector = DeadlockDetector(repetition_threshold=3)
        event = detector.check("run_tests()", "0 errors found in the last run.")
        self.assertFalse(event.is_deadlock)

if __name__ == "__main__":
    unittest.main()
