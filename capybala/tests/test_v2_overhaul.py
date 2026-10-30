"""
Test Suite for Capybala v0.2.0 Major Production Overhaul:
- Whitelist Polling Primitives
- Git SHA and Pagination Precision
- OpenAI Parallel Tool Call Atomic Pairing
- Anthropic Role Alternation Guarantee
- Grounded Diagnostic Reflection
"""

import unittest
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.api import heal, validate


class TestCapybalaOverhaul(unittest.TestCase):

    def test_git_sha_not_falsely_flagged(self):
        """Verifies that checking different git commit SHAs is never flagged as a deadlock."""
        detector = DeadlockDetector(repetition_threshold=3)
        commits = ["git checkout 3a8f9c1", "git checkout d4e2b09", "git checkout f1a2b3c"]
        for c in commits:
            event = detector.check(c, "HEAD is now at commit...")
            self.assertFalse(event.is_deadlock, f"Git SHA wrongly flagged as deadlock: {c}")

    def test_pagination_not_falsely_flagged(self):
        """Verifies that chunked file reads via line ranges are never flagged as a deadlock."""
        detector = DeadlockDetector(repetition_threshold=3)
        pages = ["sed -n '1,50p' app.py", "sed -n '51,100p' app.py", "sed -n '101,150p' app.py"]
        for p in pages:
            event = detector.check(p, "print('code')")
            self.assertFalse(event.is_deadlock, f"Pagination chunk wrongly flagged: {p}")

    def test_polling_commands_exempt(self):
        """Verifies that legitimate polling primitives (curl, kubectl, ps) are never killed."""
        detector = DeadlockDetector(repetition_threshold=3)
        for _ in range(5):
            event = detector.check("curl -s http://localhost:8000/health", "waiting...")
            self.assertFalse(event.is_deadlock, "Legitimate polling was falsely intercepted!")

    def test_openai_parallel_tool_call_atomic_rollback(self):
        """Verifies that parallel tool calls are never severed, guaranteeing zero 400 Bad Request errors."""
        pruner = ContextPruner()

        messages = [
            {"role": "system", "content": "You are a software engineer."},
            {"role": "user", "content": "Fix the authentication bug."},
            # Parallel tool call: assistant dispatches 2 calls
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": '{"path": "a.py"}'}},
                    {"id": "call_2", "type": "function", "function": {"name": "read_file", "arguments": '{"path": "b.py"}'}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "class A: pass"},
            {"role": "tool", "tool_call_id": "call_2", "content": "class B: pass"},
            # Next turn: failing repetitive tool call
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_3", "type": "function", "function": {"name": "pytest", "arguments": "{}"}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_3", "content": "FAILED: AssertionError"}
        ]

        # Execute atomic rollback
        res = pruner.rollback_and_reflect(
            messages=messages,
            failing_action="pytest",
            deadlock_details="Persistent AssertionError",
            rollback_turns=2
        )

        # Validate that no orphan tool call IDs exist
        is_valid, error = validate(res.pruned_messages)
        self.assertTrue(is_valid, f"OpenAI Schema Invariant violated: {error}")

    def test_anthropic_consecutive_user_avoided(self):
        """Verifies that Anthropic Claude's constraint (no consecutive user roles) is respected."""
        pruner = ContextPruner()

        messages = [
            {"role": "system", "content": "Assistant"},
            {"role": "user", "content": "Initial user task."}
        ]

        res = pruner.rollback_and_reflect(
            messages=messages,
            failing_action="cat file",
            deadlock_details="Deadlock",
            provider="anthropic",
            rollback_turns=1
        )

        roles = [m["role"] for m in res.pruned_messages]
        # Check that there are no consecutive 'user' roles
        for i in range(len(roles) - 1):
            if roles[i] == "user" and roles[i+1] == "user":
                self.fail(f"Anthropic violation: consecutive user roles found at index {i} and {i+1}!")

    def test_one_line_heal_api(self):
        """Verifies that `capybala.heal(messages)` seamlessly resolves deadlocks in a single line."""
        messages = [
            {"role": "system", "content": "System prompt."},
            {"role": "user", "content": "User task."},
            {"role": "assistant", "content": "pytest tests/test_core.py"},
            {"role": "tool", "content": "Traceback:\nImportError: No module named 'jwt'"},
            {"role": "assistant", "content": "pytest tests/test_core.py"},
            {"role": "tool", "content": "Traceback:\nImportError: No module named 'jwt'"},
            {"role": "assistant", "content": "pytest tests/test_core.py"},
            {"role": "tool", "content": "Traceback:\nImportError: No module named 'jwt'"}
        ]

        initial_len = len(messages)
        healed = heal(messages, repetition_threshold=3, verbose=False)
        self.assertLess(len(healed), initial_len)
        self.assertTrue(any("CAPYBALA STATE ROLLBACK" in m.get("content", "") for m in healed))


if __name__ == "__main__":
    unittest.main()

