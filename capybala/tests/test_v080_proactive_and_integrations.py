"""
test_v080_proactive_and_integrations.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Capybala v0.8.0 Major Overhaul:
1. Proactive Schema Validation & JSON Repair
2. Zero-Orphan Invariant & 400 Bad Request Prevention
3. Proactive Search Optimizer (Early Nudge Interceptor)
4. Adaptive Deadlock Policy (Exploration vs Refinement Dynamic Thresholds)
5. Universal Framework Integrations (LangGraph, CrewAI, AutoGen)
"""

import unittest
import json
from capybala.validator import repair_json_string, SchemaValidator
from capybala.proactive import SearchOptimizer
from capybala.policy import DeadlockPolicy, DeadlockMode
from capybala.detector import DeadlockDetector
from capybala.api import heal, validate, repair
from capybala.integrations.langgraph import capybala_node, CapybalaLangGraphMiddleware
from capybala.integrations.crewai import CapybalaCrewCallback
from capybala.integrations.autogen import CapybalaAutoGenFilter


class TestV080ProactiveAndIntegrations(unittest.TestCase):

    def test_repair_json_string_malformed_arguments(self):
        """Verifies deterministic JSON cleanup for malformed LLM tool call arguments."""
        # 1. Single quotes and Python booleans/None
        malformed = "{'path': 'src/main.py', 'verbose': True, 'cache': None,}"
        repaired = repair_json_string(malformed)
        parsed = json.loads(repaired)
        self.assertEqual(parsed["path"], "src/main.py")
        self.assertEqual(parsed["verbose"], True)
        self.assertIsNone(parsed["cache"])

        # 2. Missing closing braces
        unclosed = '{"command": "pytest tests/test_core.py", "timeout": 30'
        repaired_unclosed = repair_json_string(unclosed)
        parsed_unclosed = json.loads(repaired_unclosed)
        self.assertEqual(parsed_unclosed["timeout"], 30)

    def test_schema_validator_assigns_missing_tool_call_id(self):
        """Verifies that tool calls with missing IDs are proactively assigned valid IDs."""
        messages = [
            {"role": "user", "content": "Run tests"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "run_test", "arguments": '{"test": "test_auth"}'}
                        # Missing 'id'
                    }
                ]
            }
        ]
        repaired, fixes = SchemaValidator.validate_and_repair(messages)
        self.assertTrue(len(fixes) > 0)
        assigned_id = repaired[1]["tool_calls"][0]["id"]
        self.assertTrue(assigned_id.startswith("call_"))

    def test_schema_validator_heals_orphan_tool_call(self):
        """
        Verifies that an unfulfilled assistant tool_call (non-terminal) is given a
        placeholder response to eliminate OpenAI/Anthropic 400 Bad Request errors.
        """
        messages = [
            {"role": "user", "content": "Search codebase"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_stranded_123",
                        "type": "function",
                        "function": {"name": "grep", "arguments": '{"query": "User"}'}
                    }
                ]
            },
            # Non-terminal: user intervened without tool response
            {"role": "user", "content": "Actually, cancel that and check README"}
        ]
        repaired, fixes = SchemaValidator.validate_and_repair(messages)
        self.assertEqual(len(repaired), 4)
        # Synthesized tool response must be at index 2
        self.assertEqual(repaired[2]["role"], "tool")
        self.assertEqual(repaired[2]["tool_call_id"], "call_stranded_123")
        is_valid, err = validate(repaired)
        self.assertTrue(is_valid, f"Repaired messages should be strictly valid, got: {err}")

    def test_proactive_search_optimizer_early_nudge(self):
        """Verifies that 4 consecutive empty searches trigger proactive guidance."""
        optimizer = SearchOptimizer(empty_search_threshold=4)

        # Turns 1 to 3: empty greps
        for i in range(3):
            should_hint, hint = optimizer.inspect_step("grep 'UserAuth' src/", "total 0\nno matches found")
            self.assertFalse(should_hint)
            self.assertIsNone(hint)

        # Turn 4: trips threshold!
        should_hint, hint = optimizer.inspect_step("find . -name '*UserAuth*'", "no such file or directory")
        self.assertTrue(should_hint)
        self.assertIn("4 consecutive searches yielded no matches", hint)

        # Next turn: agent runs ls and finds files -> counter resets!
        should_hint, hint = optimizer.inspect_step("ls src/", "auth.py\nmain.py\nutils.py")
        self.assertFalse(should_hint)
        self.assertEqual(optimizer.consecutive_empty_searches, 0)

    def test_deadlock_policy_adaptive_mode(self):
        """Verifies dynamic sensitivity switching between Exploration and Refinement."""
        policy = DeadlockPolicy(mode=DeadlockMode.ADAPTIVE)
        detector = DeadlockDetector(policy=policy)

        # Phase 1: Exploration (reading files)
        thresh = policy.get_thresholds()
        self.assertEqual(thresh["phase"], "exploration")
        self.assertEqual(thresh["repetition_threshold"], 4)

        # 3 identical read commands with failure in Exploration phase -> NOT deadlocked (threshold is 4)
        for i in range(3):
            event = detector.check("cat non_existent_file.txt", "cat: non_existent_file.txt: No such file")
            self.assertFalse(event.is_deadlock)

        # Phase 2: Agent edits code -> shifts to Refinement!
        policy.update_action("edit src/main.py")
        thresh_refine = policy.get_thresholds()
        self.assertEqual(thresh_refine["phase"], "refinement")
        self.assertEqual(thresh_refine["repetition_threshold"], 2)

        # 2 identical edits with failing test in Refinement phase -> DEADLOCK DETECTED!
        detector.check("edit src/main.py", "SyntaxError: invalid syntax")
        event2 = detector.check("edit src/main.py", "SyntaxError: invalid syntax")
        self.assertTrue(event2.is_deadlock)
        self.assertEqual(event2.pattern_type, "direct_repetition")

    def test_langgraph_node_decorator(self):
        """Verifies LangGraph node decorator repairs state messages before execution."""
        @capybala_node
        def dummy_agent_node(state):
            # Inspect that state['messages'] were sanitized
            msgs = state["messages"]
            self.assertEqual(msgs[1]["tool_calls"][0]["function"]["arguments"], '{"key": "value"}')
            return {"messages": [{"role": "assistant", "content": "Done"}]}

        state = {
            "messages": [
                {"role": "user", "content": "Do task"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "test_fn", "arguments": "{'key': 'value',}"}  # Single quote + trailing comma
                    }]
                },
                {"role": "tool", "tool_call_id": "call_1", "content": "ok"}
            ]
        }

        output = dummy_agent_node(state)
        self.assertIn("messages", output)
        self.assertEqual(output["messages"][0]["content"], "Done")

    def test_crewai_callback_integration(self):
        """Verifies CapybalaCrewCallback detects deadlocks during CrewAI step execution."""
        callback = CapybalaCrewCallback(repetition_threshold=3)

        class MockStepOutput:
            def __init__(self, tool, tool_input, result):
                self.tool = tool
                self.tool_input = tool_input
                self.result = result

        # Simulate 3 identical failing steps
        step1 = MockStepOutput("bash", "pytest tests/test_login.py", "FAILED test_login.py - AssertionError")
        step2 = MockStepOutput("bash", "pytest tests/test_login.py", "FAILED test_login.py - AssertionError")
        step3 = MockStepOutput("bash", "pytest tests/test_login.py", "FAILED test_login.py - AssertionError")

        callback(step1)
        self.assertEqual(callback.interventions_count, 0)
        callback(step2)
        self.assertEqual(callback.interventions_count, 0)
        callback(step3)
        self.assertEqual(callback.interventions_count, 1)
        self.assertIsNotNone(callback.last_deadlock)
        self.assertEqual(callback.last_deadlock["pattern"], "direct_repetition")

    def test_autogen_filter_integration(self):
        """Verifies CapybalaAutoGenFilter attaches to an agent and validates messages."""
        guard = CapybalaAutoGenFilter()

        class MockConversableAgent:
            def __init__(self):
                self.replies = []

            def register_reply(self, trigger, reply_func, position=0):
                self.replies.append((trigger, reply_func, position))

        agent = MockConversableAgent()
        guard.attach(agent)
        self.assertEqual(len(agent.replies), 1)

        # Test reply hook with corrupted JSON in tool calls
        messages = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_abc",
                    "type": "function",
                    "function": {"name": "calc", "arguments": "{'x': 10, 'y': 20,}"}
                }]
            },
            {"role": "tool", "tool_call_id": "call_abc", "content": "30"}
        ]
        is_handled, reply = guard._reply_hook(recipient=agent, messages=messages)
        self.assertFalse(is_handled)
        # Arguments must be valid JSON double quotes
        self.assertEqual(messages[1]["tool_calls"][0]["function"]["arguments"], '{"x": 10, "y": 20}')


if __name__ == "__main__":
    unittest.main()
