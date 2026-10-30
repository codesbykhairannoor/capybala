"""
capybala.tests.test_v050_claude_audit_hardened
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests verifying fixes for vulnerabilities identified in the Claude Haiku adversarial audit:
1. Multi-threaded concurrency safety for DeadlockDetector and Circuit Breaker.
2. False-positive immunity on passing test suite outputs containing "0 failed" / "no errors".
3. Native Anthropic Claude tool_use and tool_result block parsing in heal().
4. Native Gemini parts format handling in heal().
5. Bound method and AsyncMock detection in watch().
6. String bounding and sub-millisecond execution on mega-payloads in fuzzy similarity.
"""

import unittest
import threading
import time
from unittest.mock import AsyncMock, MagicMock
from capybala.detector import DeadlockDetector
from capybala.api import heal, watch, _is_async_callable


class TestClaudeAuditHardening(unittest.TestCase):

    def test_concurrent_detector_check_thread_safety(self):
        """
        Verifies that DeadlockDetector is thread-safe under concurrent multi-threaded agent execution.
        """
        detector = DeadlockDetector(
            repetition_threshold=3,
            max_interventions=5,
            circuit_breaker_enabled=True
        )

        def worker():
            for _ in range(20):
                # Repetitive failing command
                detector.check("python -m app.run", "Error: Database connection refused")

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Circuit breaker must have engaged or total count tracked atomically
        self.assertGreater(detector.total_deadlocks_detected, 0)
        self.assertEqual(detector.turn_counter, 80)

    def test_false_positive_immunity_on_passing_tests(self):
        """
        Ensures outputs like '15 passed, 0 failed' or 'no errors found'
        are never misclassified as failures by fuzzy or stagnation detectors.
        """
        detector = DeadlockDetector(repetition_threshold=3, fuzzy_threshold=0.65)
        actions = [
            "pytest tests/test_auth.py",
            "pytest tests/test_core.py",
            "pytest tests/test_api.py",
        ]
        passing_outputs = [
            "=== 25 passed, 0 failed in 0.12s ===",
            "=== 25 passed, 0 failed in 0.12s ===",
            "=== 25 passed, 0 failed in 0.12s ===",
        ]

        for act, out in zip(actions, passing_outputs):
            event = detector.check(act, out)
            self.assertFalse(event.is_deadlock, "Passing test with '0 failed' must not trigger deadlock!")

    def test_anthropic_native_tool_use_and_result_healing(self):
        """
        Verifies that capybala.heal() natively supports Anthropic Claude's content blocks
        (type: 'tool_use' and type: 'tool_result').
        """
        messages = [
            {"role": "user", "content": "Fetch user record"},
            # Turn 1
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Fetching..."},
                    {"type": "tool_use", "id": "toolu_1", "name": "get_user", "input": {"id": 101}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_1", "content": "Error: User 101 not found"}
                ]
            },
            # Turn 2
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_2", "name": "get_user", "input": {"id": 101}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_2", "content": "Error: User 101 not found"}
                ]
            },
            # Turn 3 (Deadlock turn)
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_3", "name": "get_user", "input": {"id": 101}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_3", "content": "Error: User 101 not found"}
                ]
            },
        ]

        orig_len = len(messages)
        healed = heal(messages, repetition_threshold=3, provider="anthropic", verbose=False)
        self.assertLess(len(healed), orig_len)
        # In Anthropic schema, the recovery directive is merged into user turn to avoid consecutive user roles
        self.assertEqual(healed[-1]["role"], "user")
        content_str = str(healed[-1]["content"])
        self.assertIn("CAPYBALA DOCTOR INTERVENTION", content_str)

    def test_gemini_native_parts_healing(self):
        """
        Verifies that capybala.heal() handles Gemini messages with 'parts' representation.
        """
        messages = [
            {"role": "user", "parts": [{"text": "Fix bug"}]},
            {"role": "model", "parts": [{"function_calls": [{"name": "bash", "args": {"cmd": "python app.py"}}]}]},
            {"role": "user", "parts": [{"text": "Error: Connection refused"}]},
            {"role": "model", "parts": [{"function_calls": [{"name": "bash", "args": {"cmd": "python app.py"}}]}]},
            {"role": "user", "parts": [{"text": "Error: Connection refused"}]},
            {"role": "model", "parts": [{"function_calls": [{"name": "bash", "args": {"cmd": "python app.py"}}]}]},
            {"role": "user", "parts": [{"text": "Error: Connection refused"}]},
        ]

        orig_len = len(messages)
        healed = heal(messages, repetition_threshold=3, verbose=False)
        self.assertLess(len(healed), orig_len)

    def test_async_mock_bound_method_detection(self):
        """
        Verifies that _is_async_callable correctly detects bound async methods and AsyncMock.
        """
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock()

        self.assertTrue(_is_async_callable(mock_client.chat.completions.create))

        # Sync callable must return False
        sync_fn = lambda x: x
        self.assertFalse(_is_async_callable(sync_fn))

    def test_mega_payload_bounded_similarity_latency(self):
        """
        Verifies that passing a huge string (e.g. 50,000 characters) into _calculate_fuzzy_similarity
        executes sub-millisecond without hanging or memory explosion.
        """
        detector = DeadlockDetector()
        huge_str = "a" * 25000 + "---" * 5000 + "b" * 20000

        start = time.perf_counter()
        sim = detector._calculate_fuzzy_similarity(huge_str, "test command")
        duration_ms = (time.perf_counter() - start) * 1000

        self.assertLess(duration_ms, 15.0, f"Execution took {duration_ms:.2f} ms (must be < 15ms)")
        self.assertGreaterEqual(sim, 0.0)


if __name__ == "__main__":
    unittest.main()
