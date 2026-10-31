"""
capybala.tests.test_v091_enterprise_shadow_and_canonical
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Capybala v0.9.1:
1. Enterprise Shadow Mode:
   - Verifies zero-risk observability mode (detects deadlocks without mutating messages).
   - Verifies circuit breaker candidates in shadow mode.
2. Live Cache Telemetry Extractor:
   - Verifies extraction of Anthropic cache_read_input_tokens and OpenAI cached_tokens.
3. Canonical Action Intent Normalizer:
   - Verifies cross-syntax equivalence for grep vs find | xargs grep vs rg.
   - Verifies boosted fuzzy similarity and semantic attractor features.
"""

import unittest
from capybala.detector import DeadlockDetector, canonicalize_action_intent
from capybala.api import heal, extract_cache_telemetry


class MockAnthropicResponse:
    def __init__(self, cache_read: int, cache_creation: int, input_tokens: int):
        class Usage:
            def __init__(self, cr, cc, inp):
                self.cache_read_input_tokens = cr
                self.cache_creation_input_tokens = cc
                self.input_tokens = inp
        self.usage = Usage(cache_read, cache_creation, input_tokens)


class MockOpenAIResponse:
    def __init__(self, cached_tokens: int, prompt_tokens: int):
        class Details:
            def __init__(self, ct):
                self.cached_tokens = ct
        class Usage:
            def __init__(self, ct, pt):
                self.prompt_tokens_details = Details(ct)
                self.prompt_tokens = pt
        self.usage = Usage(cached_tokens, prompt_tokens)


class TestV091EnterpriseShadowAndCanonical(unittest.TestCase):

    def test_canonical_action_intent_search(self):
        """Verifies grep, find | xargs grep, and rg normalize to the identical search intent."""
        act_grep = "grep -rn 'UserModel' /app/src/models"
        act_find = "find /app/src/models -name '*.py' | xargs grep 'UserModel'"
        act_rg = "rg 'UserModel' /app/src/models"

        intent_grep = canonicalize_action_intent(act_grep)
        intent_find = canonicalize_action_intent(act_find)
        intent_rg = canonicalize_action_intent(act_rg)

        self.assertTrue(intent_grep.startswith("INTENT:SEARCH"))
        self.assertEqual(intent_grep, intent_find)
        self.assertEqual(intent_grep, intent_rg)
        self.assertIn("usermodel", intent_grep)
        self.assertIn("/app/src/models", intent_grep)

    def test_canonical_action_intent_boosts_fuzzy_similarity(self):
        """Verifies that grep vs find|xargs grep achieves high similarity via canonical intent."""
        detector = DeadlockDetector()
        act_grep = "grep -rn 'UserModel' /app/src/models"
        act_find = "find /app/src/models -name '*.py' | xargs grep 'UserModel'"

        sim = detector._calculate_fuzzy_similarity(act_grep, act_find)
        self.assertGreaterEqual(sim, 0.85)

    def test_canonical_action_intent_test_and_read(self):
        """Verifies pytest and cat/view normalizations."""
        test_act1 = "python -m pytest tests/test_core.py"
        test_act2 = "pytest tests/test_core.py -v"
        self.assertEqual(
            canonicalize_action_intent(test_act1),
            canonicalize_action_intent(test_act2)
        )

        read_act1 = "cat src/models.py"
        read_act2 = "head -n 50 src/models.py"
        self.assertEqual(
            canonicalize_action_intent(read_act1),
            canonicalize_action_intent(read_act2)
        )

    def test_detector_shadow_mode(self):
        """Verifies that DeadlockDetector in shadow mode marks events as is_shadow=True."""
        detector = DeadlockDetector(repetition_threshold=3, shadow_mode=True)
        detector.check("ls -la /bad", "Error 404")
        detector.check("ls -la /bad", "Error 404")
        evt = detector.check("ls -la /bad", "Error 404")

        self.assertTrue(evt.is_deadlock)
        self.assertTrue(evt.is_shadow)
        self.assertIn("[SHADOW MODE]", evt.details)

    def test_heal_shadow_mode_does_not_mutate_messages(self):
        """Verifies heal(messages, shadow_mode=True) detects deadlocks but leaves messages 100% unmutated."""
        # Create a looping message history
        messages = [
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": "Run tests."},
            {"role": "assistant", "content": "Running test.", "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "run", "arguments": "{\"cmd\": \"pytest\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "FAILED"},
            {"role": "assistant", "content": "Retrying test.", "tool_calls": [{"id": "c2", "type": "function", "function": {"name": "run", "arguments": "{\"cmd\": \"pytest\"}"}}]},
            {"role": "tool", "tool_call_id": "c2", "content": "FAILED"},
            {"role": "assistant", "content": "Retrying test again.", "tool_calls": [{"id": "c3", "type": "function", "function": {"name": "run", "arguments": "{\"cmd\": \"pytest\"}"}}]},
            {"role": "tool", "tool_call_id": "c3", "content": "FAILED"},
        ]
        original_len = len(messages)
        original_last_content = messages[-1]["content"]

        # Run in SHADOW MODE
        res = heal(messages, repetition_threshold=3, shadow_mode=True, verbose=False)

        # Messages must be untouched
        self.assertEqual(len(messages), original_len)
        self.assertEqual(messages[-1]["content"], original_last_content)
        self.assertEqual(len(res), original_len)

        # Run in ACTIVE MODE
        res_active = heal(messages, repetition_threshold=3, shadow_mode=False, verbose=False)
        # In active mode, rollback occurred and reflection was injected
        self.assertLess(len(res_active), original_len + 1)
        self.assertTrue(any("CAPYBALA STATE ROLLBACK" in str(m.get("content")) for m in res_active))

    def test_extract_cache_telemetry_anthropic(self):
        """Verifies cache extraction from Anthropic responses."""
        resp = MockAnthropicResponse(cache_read=8000, cache_creation=500, input_tokens=1500)
        tel = extract_cache_telemetry(resp)
        self.assertIsNotNone(tel)
        self.assertEqual(tel["provider"], "anthropic")
        self.assertEqual(tel["cached_tokens"], 8000)
        self.assertEqual(tel["total_prompt_tokens"], 10000)
        self.assertEqual(tel["cache_hit_rate"], 80.0)

    def test_extract_cache_telemetry_openai(self):
        """Verifies cache extraction from OpenAI responses."""
        resp = MockOpenAIResponse(cached_tokens=4500, prompt_tokens=5000)
        tel = extract_cache_telemetry(resp)
        self.assertIsNotNone(tel)
        self.assertEqual(tel["provider"], "openai")
        self.assertEqual(tel["cached_tokens"], 4500)
        self.assertEqual(tel["total_prompt_tokens"], 5000)
        self.assertEqual(tel["cache_hit_rate"], 90.0)


if __name__ == "__main__":
    unittest.main()
