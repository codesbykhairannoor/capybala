"""
capybala.tests.test_v041_advanced_detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Advanced Detection Capabilities (v0.5.0):
1. Fuzzy Polymorphic Loop Detection (token Jaccard + 3-gram character shingles).
2. Multi-Agent Delegation Ping-Pong & Cycle Detection (LangGraph / CrewAI / AutoGen).
3. Observation / Output Stagnation Detection with Polling Whitelist Exemption.
4. Prescriptive Guidance for Polymorphic and Delegation Deadlocks.
5. End-to-end atomic rollback and healing for fuzzy polymorphic loops.
"""

import unittest
from capybala.detector import DeadlockDetector, DeadlockEvent
from capybala.healer import AgentHealer
from capybala.api import heal


class TestAdvancedDetectionV050(unittest.TestCase):

    def setUp(self):
        self.detector = DeadlockDetector(
            repetition_threshold=3,
            oscillation_threshold=2,
            fuzzy_threshold=0.65,
        )
        self.healer = AgentHealer()

    def test_fuzzy_polymorphic_repetition_cli_flags(self):
        """
        Detects loops where an agent repeatedly runs variants of the same failing command
        by tweaking CLI flags or parameters (e.g. pytest flags).
        """
        # Turn 1
        ev1 = self.detector.check(
            "pytest tests/test_auth.py -v",
            "FAILED tests/test_auth.py::test_login - AssertionError: Expected 200 got 500"
        )
        self.assertFalse(ev1.is_deadlock)

        # Turn 2: tweak flags
        ev2 = self.detector.check(
            "pytest tests/test_auth.py --capture=no",
            "FAILED tests/test_auth.py::test_login - AssertionError: Expected 200 got 500"
        )
        self.assertFalse(ev2.is_deadlock)

        # Turn 3: tweak flags again
        ev3 = self.detector.check(
            "pytest tests/test_auth.py -v -k 'login'",
            "FAILED tests/test_auth.py::test_login - AssertionError: Expected 200 got 500"
        )
        self.assertTrue(ev3.is_deadlock)
        self.assertEqual(ev3.pattern_type, "fuzzy_repetition")
        self.assertIn("Polymorphic command loop", ev3.details)

    def test_fuzzy_repetition_not_flagged_on_success(self):
        """
        Ensures polymorphic variations that SUCCEED without errors are never falsely flagged.
        Zero false positive verification.
        """
        actions = [
            "python script.py --step 1",
            "python script.py --step 2",
            "python script.py --step 3",
            "python script.py --step 4",
        ]
        for act in actions:
            ev = self.detector.check(act, "SUCCESS: step processed cleanly.")
            self.assertFalse(ev.is_deadlock)

    def test_multi_agent_delegation_ping_pong_period2(self):
        """
        Detects 2-agent ping-pong delegation cycles (Agent A <-> Agent B).
        Common failure mode in CrewAI, LangGraph, and AutoGen.
        """
        # Turn 1: Manager -> Researcher
        ev1 = self.detector.check(
            'delegate_to(agent="researcher", task="find root cause")',
            "Task dispatched to researcher."
        )
        self.assertFalse(ev1.is_deadlock)

        # Turn 2: Researcher -> Coder
        ev2 = self.detector.check(
            'delegate_to(agent="coder", task="apply fix")',
            "Task dispatched to coder."
        )
        self.assertFalse(ev2.is_deadlock)

        # Turn 3: Coder -> Researcher (ping-pong turn 1)
        ev3 = self.detector.check(
            'delegate_to(agent="researcher", task="verify tests")',
            "Task dispatched to researcher."
        )
        self.assertFalse(ev3.is_deadlock)

        # Turn 4: Researcher -> Coder (ping-pong cycle completed: researcher <-> coder)
        ev4 = self.detector.check(
            'delegate_to(agent="coder", task="fix is still failing")',
            "Task dispatched to coder."
        )
        self.assertTrue(ev4.is_deadlock)
        self.assertEqual(ev4.pattern_type, "delegation_cycle")
        self.assertIn("researcher", ev4.details)
        self.assertIn("coder", ev4.details)

    def test_multi_agent_delegation_cycle_period3(self):
        """
        Detects 3-agent circular delegation cycles (A -> B -> C -> A -> B -> C).
        """
        agents = ["planner", "coder", "reviewer", "planner", "coder", "reviewer"]
        last_ev = None
        for i, ag in enumerate(agents):
            last_ev = self.detector.check(
                f'transfer_to_agent(recipient="{ag}", message="handoff {i}")',
                f"Handoff to {ag} acknowledged."
            )
        self.assertIsNotNone(last_ev)
        self.assertTrue(last_ev.is_deadlock)
        self.assertEqual(last_ev.pattern_type, "delegation_cycle")
        self.assertIn("3-agent loop", last_ev.details)

    def test_delegation_not_flagged_on_linear_pipeline(self):
        """
        Linear multi-agent handoffs without cycles (A -> B -> C -> D) must never be flagged.
        """
        pipeline = ["planner", "researcher", "coder", "tester", "deployer"]
        for ag in pipeline:
            ev = self.detector.check(
                f'delegate_to(agent="{ag}", task="step")',
                f"Handled by {ag}"
            )
            self.assertFalse(ev.is_deadlock)

    def test_observation_stagnation_deadlock(self):
        """
        Detects when an agent attempts different commands, but the environment
        produces identical failing output across consecutive turns.
        """
        failing_output = "Error: Database connection refused on port 5432. Server is offline."

        ev1 = self.detector.check("python -m app", failing_output)
        self.assertFalse(ev1.is_deadlock)

        ev2 = self.detector.check("python app/main.py", failing_output)
        self.assertFalse(ev2.is_deadlock)

        ev3 = self.detector.check("python3 app/main.py", failing_output)
        self.assertTrue(ev3.is_deadlock)
        self.assertEqual(ev3.pattern_type, "output_stagnation")
        self.assertIn("Observation stagnation deadlock", ev3.details)

    def test_observation_stagnation_exempt_for_polling(self):
        """
        Legitimate polling commands (curl, ps, kubectl) returning identical output
        must remain exempt from output stagnation deadlock.
        """
        stagnant_poll_output = "HTTP/1.1 503 Service Unavailable\r\nRetry-After: 5"

        for _ in range(5):
            ev = self.detector.check("curl http://localhost:8080/health", stagnant_poll_output)
            self.assertFalse(ev.is_deadlock)

    def test_fuzzy_and_delegation_healer_prescriptions(self):
        """
        Verifies that AgentHealer generates decisive, domain-specific prescriptions
        for fuzzy polymorphic loops and multi-agent delegation cycles.
        """
        # Fuzzy prescription
        rx_fuzzy = self.healer.prescribe(
            deadlock_pattern="fuzzy_repetition",
            failing_action="pytest tests/test_core.py -v -k 'test_run'",
            error_signature="AssertionError: Expected 200 got 500",
        )
        self.assertIn("Polymorphic action repetition", rx_fuzzy.recommended_pivot)
        self.assertIn("Stop tweaking flags", rx_fuzzy.recommended_pivot)

        # Delegation prescription
        rx_del = self.healer.prescribe(
            deadlock_pattern="delegation_cycle",
            failing_action='delegate_to(agent="coder")',
            error_signature="",
        )
        self.assertIn("delegation cycle", rx_del.recommended_pivot)
        self.assertIn("Do NOT delegate", rx_del.recommended_pivot)
        self.assertIn("decisive local ownership", rx_del.recommended_pivot)

    def test_end_to_end_heal_with_fuzzy_loop(self):
        """
        Verifies that capybala.heal() intercepts polymorphic loops in full OpenAI messages
        and rolls back history atomically with actionable reflection.
        """
        messages = [
            {"role": "system", "content": "You are a senior engineer."},
            {"role": "user", "content": "Fix the authentication bug."},
            # Turn 1
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "run_test", "arguments": '{"cmd": "pytest tests/test_auth.py -v"}'}
                }]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "FAILED tests/test_auth.py - AssertionError: 401 != 200"},
            # Turn 2
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "run_test", "arguments": '{"cmd": "pytest tests/test_auth.py --capture=no"}'}
                }]
            },
            {"role": "tool", "tool_call_id": "call_2", "content": "FAILED tests/test_auth.py - AssertionError: 401 != 200"},
            # Turn 3 (Polymorphic loop completion)
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_3",
                    "type": "function",
                    "function": {"name": "run_test", "arguments": '{"cmd": "pytest tests/test_auth.py -v -k \\"login\\""}'}
                }]
            },
            {"role": "tool", "tool_call_id": "call_3", "content": "FAILED tests/test_auth.py - AssertionError: 401 != 200"},
        ]

        original_len = len(messages)
        healed_messages = heal(messages, repetition_threshold=3, verbose=False)

        # Must have performed atomic rollback and injected Doctor intervention
        self.assertLess(len(healed_messages), original_len)
        last_msg = healed_messages[-1]
        self.assertEqual(last_msg["role"], "user")
        self.assertIn("CAPYBALA DOCTOR INTERVENTION", last_msg["content"])
        self.assertIn("Polymorphic", last_msg["content"])


if __name__ == "__main__":
    unittest.main()
