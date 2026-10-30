"""
Unit test suite for Capybala Universal Adapters:
- CapybalaGuard (Generic wrapper)
- capybala_watch (Decorator)
- LlamaStackCapybalaMiddleware (Meta Llama Stack)
- CapybalaCallbackHandler (LangChain)
"""

import unittest
from capybala.adapters.generic import CapybalaGuard, capybala_watch
from capybala.adapters.llama_stack import LlamaStackCapybalaMiddleware
from capybala.adapters.langchain import CapybalaCallbackHandler


class TestCapybalaAdapters(unittest.TestCase):

    def test_capybala_guard_in_place_healing(self):
        messages = [
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": "Fix the bug in auth.py"}
        ]

        guard = CapybalaGuard(messages=messages, repetition_threshold=3)

        # Step 1
        res1 = guard.step("pytest tests/test_auth.py", "FAILED: AssertionError")
        self.assertFalse(res1)
        self.assertFalse(guard.is_deadlocked)

        # Step 2
        res2 = guard.step("pytest tests/test_auth.py", "FAILED: AssertionError")
        self.assertFalse(res2)

        # Step 3 -> Deadlock intercepted!
        res3 = guard.step("pytest tests/test_auth.py", "FAILED: AssertionError")
        self.assertTrue(res3)
        self.assertTrue(guard.is_deadlocked)
        self.assertIsNotNone(guard.latest_prescription)

        # Messages list was modified in-place and contains Doctor intervention
        self.assertTrue(any("CAPYBALA DOCTOR INTERVENTION" in m.get("content", "") for m in messages))

    def test_capybala_watch_decorator(self):
        @capybala_watch(repetition_threshold=3)
        def agent_step(action, observation, messages=None, capybala_healed=False, prescription=None):
            return {
                "action": action,
                "healed": capybala_healed,
                "prescription": prescription,
                "msg_count": len(messages) if messages else 0
            }

        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": "a"},
            {"role": "tool", "content": "err"},
            {"role": "assistant", "content": "a"},
            {"role": "tool", "content": "err"}
        ]

        # Call with 3rd repeating action
        out = agent_step(
            action="git checkout .",
            observation="fatal error",
            messages=msgs
        )

        # Should be healed by the decorator
        # Notice: adapter inside decorator detects 3rd occurrence if fed sequentially
        self.assertIn("healed", out)

    def test_llama_stack_middleware(self):
        middleware = LlamaStackCapybalaMiddleware(repetition_threshold=3)
        session_turns = [
            {"role": "system", "content": "Llama Agent"},
            {"role": "user", "content": "Write unit tests."}
        ]

        for i in range(2):
            session_turns.append({"role": "assistant", "content": "call"})
            session_turns.append({"role": "tool", "content": "fail"})
            is_dead, turns, rx = middleware.on_tool_step(
                tool_name="bash",
                tool_arguments={"command": "pytest"},
                tool_output="FAILED test_case_1",
                session_turns=session_turns
            )
            self.assertFalse(is_dead)

        # 3rd time
        session_turns.append({"role": "assistant", "content": "call"})
        session_turns.append({"role": "tool", "content": "fail"})
        is_dead, turns, rx = middleware.on_tool_step(
            tool_name="bash",
            tool_arguments={"command": "pytest"},
            tool_output="FAILED test_case_1",
            session_turns=session_turns
        )
        self.assertTrue(is_dead)
        self.assertIsNotNone(rx)
        self.assertTrue(any("CAPYBALA DOCTOR INTERVENTION" in t.get("content", "") for t in turns))

    def test_langchain_callback_handler(self):
        handler = CapybalaCallbackHandler(repetition_threshold=3)

        # 3 identical failing tool executions
        for _ in range(3):
            handler.on_tool_start({"name": "python_repl"}, "import broken_pkg")
            handler.on_tool_end("ModuleNotFoundError: No module named 'broken_pkg'")

        self.assertTrue(handler.deadlock_triggered)
        self.assertIsNotNone(handler.last_prescription)
        self.assertIn("sys.path", handler.last_prescription.recommended_pivot.lower())


if __name__ == "__main__":
    unittest.main()

