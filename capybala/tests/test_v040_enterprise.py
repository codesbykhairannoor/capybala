"""
Unit test suite for Capybala v0.4.0 Enterprise Hardening:
- Circuit Breaker & Meta-Deadlock Prevention (DeadlockEmergencyStop)
- Volatile JSON Argument Normalization (Timestamps, Nonces, Request IDs)
- Progressive Escalation Healer (Anti-Autoregressive Echo)
- Universal Input Sanitization & Defensive Invariants
- Anthropic Turn Alternation Protocol Validator
- Streaming Request Passthrough
"""

import unittest
import json
import capybala as cb
from capybala.detector import DeadlockDetector, DeadlockEmergencyStop
from capybala.healer import AgentHealer
from capybala.api import heal, watch, validate


class TestV040EnterpriseHardening(unittest.TestCase):

    def test_circuit_breaker_tripping(self):
        """Verifies that an agent looping repeatedly trips the circuit breaker after max_interventions."""
        detector = DeadlockDetector(
            repetition_threshold=3,
            max_interventions=3,
            circuit_breaker_enabled=True
        )

        # Loop 1: Action A fails 3x
        for _ in range(3):
            ev1 = detector.check("pytest tests/test_core.py", "FAILED: 1 error")
        self.assertTrue(ev1.is_deadlock)
        self.assertFalse(ev1.is_circuit_broken)
        self.assertEqual(detector.consecutive_deadlocks, 1)

        # Loop 2: Action B fails 3x
        for _ in range(3):
            ev2 = detector.check("pytest tests/test_auth.py", "FAILED: auth error")
        self.assertTrue(ev2.is_deadlock)
        self.assertFalse(ev2.is_circuit_broken)
        self.assertEqual(detector.consecutive_deadlocks, 2)

        # Loop 3: Action C fails 3x -> Circuit Breaker trips!
        for _ in range(3):
            ev3 = detector.check("pytest tests/test_db.py", "FAILED: db error")
        self.assertTrue(ev3.is_deadlock)
        self.assertTrue(ev3.is_circuit_broken)
        self.assertIn("CIRCUIT BREAKER TRIPPED", ev3.details)

    def test_emergency_stop_exception_raising(self):
        """Verifies that heal(..., raise_on_circuit_break=True) raises DeadlockEmergencyStop."""
        history = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Fix bug."},
            {"role": "assistant", "content": "pytest"},
            {"role": "tool", "content": "FAILED"},
            {"role": "assistant", "content": "pytest"},
            {"role": "tool", "content": "FAILED"},
            {"role": "assistant", "content": "pytest"},
            {"role": "tool", "content": "FAILED"},
        ]

        with self.assertRaises(DeadlockEmergencyStop):
            heal(
                history,
                repetition_threshold=3,
                max_interventions=1,
                circuit_breaker=True,
                raise_on_circuit_break=True,
                verbose=False
            )

    def test_circuit_breaker_reset_on_healthy_progression(self):
        """Verifies that consecutive deadlock counter decays to 0 upon healthy progress."""
        detector = DeadlockDetector(repetition_threshold=3, max_interventions=3)

        # Trigger 1 deadlock
        for _ in range(3):
            detector.check("pytest", "FAILED")
        self.assertEqual(detector.consecutive_deadlocks, 1)

        # 3 healthy turns
        detector.check("git diff", "diff output")
        detector.check("cat file.py", "contents")
        detector.check("ls src/", "src contents")

        # Counter should reset to 0
        self.assertEqual(detector.consecutive_deadlocks, 0)

    def test_dynamic_json_volatile_sanitization(self):
        """Verifies that dynamic timestamps and nonces in JSON arguments do not blind the detector."""
        detector = DeadlockDetector(repetition_threshold=3)

        # Actions have identical commands but varying dynamic timestamps and nonces
        act1 = json.dumps({"command": "pytest tests/test_api.py", "timestamp": "2026-10-30T14:00:01Z", "nonce": 111})
        act2 = json.dumps({"command": "pytest tests/test_api.py", "timestamp": "2026-10-30T14:00:02Z", "nonce": 222})
        act3 = json.dumps({"command": "pytest tests/test_api.py", "timestamp": "2026-10-30T14:00:03Z", "nonce": 333})

        detector.check(f"bash({act1})", "FAILED: assertion error")
        detector.check(f"bash({act2})", "FAILED: assertion error")
        ev = detector.check(f"bash({act3})", "FAILED: assertion error")

        self.assertTrue(ev.is_deadlock)
        self.assertEqual(ev.pattern_type, "direct_repetition")

    def test_iso8601_tz_offsets_and_epoch_timestamps(self):
        """Verifies normalization of ISO8601 with timezone offsets and Unix epoch timestamps."""
        detector = DeadlockDetector()
        text = "Error at 2026-10-30T14:15:30.456+07:00 with epoch 1730300000 on pointer 0x7fff5fbff820"
        normalized = detector._normalize_text(text)

        self.assertIn("<TIMESTAMP>", normalized)
        self.assertIn("<EPOCH_TS>", normalized)
        self.assertIn("<PTR_ADDR>", normalized)
        self.assertNotIn("2026-10-30", normalized)
        self.assertNotIn("1730300000", normalized)

    def test_progressive_escalation_healer(self):
        """Verifies that repeated failures trigger high-escalation radical reset directives."""
        healer = AgentHealer()

        # Level 1 intervention
        rx1 = healer.prescribe(
            deadlock_pattern="direct_repetition",
            failing_action="pytest",
            error_signature="AssertionError",
            escalation_level=1
        )
        self.assertNotIn("CRITICAL ESCALATION", rx1.recommended_pivot)

        # Level 3 intervention
        rx3 = healer.prescribe(
            deadlock_pattern="direct_repetition",
            failing_action="pytest",
            error_signature="AssertionError",
            escalation_level=3
        )
        self.assertIn("CRITICAL ESCALATION - Level 3", rx3.recommended_pivot)

    def test_streaming_wrapper_passthrough(self):
        """Verifies that watch() cleanly handles streaming completions (stream=True)."""
        class MockClient:
            def __init__(self):
                self.chat = self.Chat()
            class Chat:
                def __init__(self):
                    self.completions = self.Completions()
                class Completions:
                    def create(self, *args, **kwargs):
                        if kwargs.get("stream"):
                            return iter([{"token": "chunk1"}, {"token": "chunk2"}])
                        return {"role": "assistant", "content": "full"}

        client = cb.watch(MockClient())
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        stream_res = client.chat.completions.create(messages=messages, stream=True)
        chunks = list(stream_res)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["token"], "chunk1")

    def test_validate_anthropic_turn_alternation(self):
        """Verifies that validate() detects consecutive user/assistant role violations for Anthropic."""
        invalid_history = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "Are you there?"}
        ]
        is_valid, err = validate(invalid_history, check_turn_alternation=True)
        self.assertFalse(is_valid)
        self.assertIn("Consecutive 'user' roles detected", err)

        valid_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Yes, I am here."},
            {"role": "user", "content": "Next step."}
        ]
        is_valid, err = validate(valid_history, check_turn_alternation=True)
        self.assertTrue(is_valid)

    def test_malformed_input_resilience(self):
        """Verifies that heal() gracefully ignores corrupted non-dict messages without crashing."""
        corrupted_history = [
            {"role": "system", "content": "sys"},
            "CORRUPTED_STRING_NOT_A_DICT",
            None,
            42,
            {"role": "user", "content": "task"},
            {"role": "assistant", "content": "act"},
            {"role": "tool", "content": "err"},
            {"role": "assistant", "content": "act"},
            {"role": "tool", "content": "err"},
            {"role": "assistant", "content": "act"},
            {"role": "tool", "content": "err"},
        ]
        healed = heal(corrupted_history, verbose=False)
        self.assertIs(healed, corrupted_history)
        self.assertTrue(len(healed) > 0)


if __name__ == "__main__":
    unittest.main()
