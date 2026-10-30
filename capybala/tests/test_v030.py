"""
Unit tests for Capybala v0.3.0:
- AsyncIO / coroutine signature preservation
- In-place list mutation (ghost pruning desync prevention)
- Deep copy isolation
- OpenAI parallel tool call atomic rewind
- Polling command whitelist exemption
- Universal schema adherence (no mid-stream system role)
- Period-2 and Period-3 oscillation detection
"""

import unittest
import asyncio
import inspect
import copy
from unittest.mock import MagicMock, AsyncMock

import capybala as cb
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.api import heal, watch, validate


class TestV030Engine(unittest.TestCase):
    def setUp(self):
        self.detector = DeadlockDetector(repetition_threshold=3, oscillation_threshold=2)
        self.pruner = ContextPruner()

    def test_polling_whitelist_exemption(self):
        """Commands like curl, kubectl, docker wait should not trigger deadlock even if output repeats."""
        for _ in range(5):
            ev = self.detector.check("bash({'command': 'curl -s https://api.internal/health'})", "status: waiting")
            self.assertFalse(ev.is_deadlock)

        for _ in range(5):
            ev = self.detector.check("kubectl get pods -l app=indexer", "PodInitializing")
            self.assertFalse(ev.is_deadlock)

    def test_period_3_oscillation(self):
        """A -> B -> C -> A -> B -> C loop detection."""
        detector = DeadlockDetector()
        actions = [
            "git stash", "pip install -e .", "pytest tests/",
            "git stash", "pip install -e .", "pytest tests/"
        ]
        ev = None
        for a in actions:
            ev = detector.check(a, "error encountered")

        self.assertTrue(ev.is_deadlock)
        self.assertEqual(ev.pattern_type, "oscillation")

    def test_in_place_mutation_prevents_ghost_pruning(self):
        """Ensures developer outer history list is modified in-place."""
        history = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Solve issue."},
            {"role": "assistant", "content": "Running test..."},
            {"role": "tool", "tool_call_id": "c1", "content": "ImportError: No module named foo"},
            {"role": "assistant", "content": "Running test..."},
            {"role": "tool", "tool_call_id": "c2", "content": "ImportError: No module named foo"},
            {"role": "assistant", "content": "Running test..."},
            {"role": "tool", "tool_call_id": "c3", "content": "ImportError: No module named foo"},
        ]
        original_ref = history
        healed = cb.heal(history, repetition_threshold=3, verbose=False)

        # Both the returned list and original list reference must be updated
        self.assertIs(healed, original_ref)
        self.assertLess(len(history), 8)
        # Verify no mid-stream system role was introduced
        for msg in history[1:]:
            self.assertNotEqual(msg.get("role"), "system")

    def test_deep_copy_isolation(self):
        """Ensures caller message objects are not mutated when rollback occurs."""
        original_user_msg = {"role": "user", "content": "Initial instruction"}
        history = [
            {"role": "system", "content": "System prompt"},
            original_user_msg,
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c1", "content": "Error"},
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c2", "content": "Error"},
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c3", "content": "Error"},
        ]

        # Keep a snapshot of original_user_msg
        user_msg_content_before = original_user_msg["content"]
        res = self.pruner.rollback_and_reflect(history, "action1", "deadlock", rollback_turns=4)

        # The initial user prompt must remain pristine
        self.assertEqual(original_user_msg["content"], user_msg_content_before)

    def test_openai_parallel_tool_call_atomic_rollback(self):
        """Atomic rollback must unwind past assistant tool-calling turn to prevent orphan tool responses."""
        history = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User task"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "function": {"name": "read", "arguments": "{}"}},
                {"id": "call_2", "function": {"name": "grep", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "call_1", "content": "result 1"},
            {"role": "tool", "tool_call_id": "call_2", "content": "result 2"},
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c3", "content": "Error"},
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c4", "content": "Error"},
            {"role": "assistant", "content": "action1"},
            {"role": "tool", "tool_call_id": "c5", "content": "Error"},
        ]

        healed = cb.heal(history, repetition_threshold=3, verbose=False)
        is_valid, err = validate(healed)
        self.assertTrue(is_valid, f"Validation failed: {err}")

    def test_asyncio_wrapper_preserves_coroutine_signature(self):
        """watch(async_client) must maintain inspect.iscoroutinefunction() and not strip it."""
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()

        # Set up an async coroutine function
        async def fake_async_create(*args, **kwargs):
            return {"role": "assistant", "content": "ok"}

        mock_client.chat.completions.create = fake_async_create
        self.assertTrue(inspect.iscoroutinefunction(mock_client.chat.completions.create))

        # Apply watch
        watched_client = watch(mock_client)
        self.assertTrue(
            inspect.iscoroutinefunction(watched_client.chat.completions.create),
            "watch() stripped inspect.iscoroutinefunction signature on AsyncOpenAI client!"
        )

        # Ensure idempotency (no double-wrapping cascade)
        watched_again = watch(watched_client)
        self.assertIs(watched_again, watched_client)


if __name__ == "__main__":
    unittest.main()
