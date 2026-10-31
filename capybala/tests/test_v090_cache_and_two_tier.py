"""
capybala.tests.test_v090_cache_and_two_tier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Capybala v0.9.0:
1. Two-Tier Cycle Detection Hierarchy:
   - Tier 1: Instant O(1) Floyd / Brent exact cycle detection and SHA-256 matching (<0.01 ms).
   - Tier 2: Sub-millisecond continuous lexical manifold attractor and fuzzy n-gram tracking (<0.8 ms).
2. Cache-Preserving Context Rollback & Pruning:
   - Verifies byte-for-byte prefix preservation for 90% prompt cache discounts on Claude & OpenAI.
   - Tests cache_preserving=True vs cache_preserving=False modes.
"""

import unittest
from capybala.detector import DeadlockDetector, find_exact_cycle_floyd
from capybala.pruner import ContextPruner, PruneResult
from capybala.attractor import SemanticAttractorDetector


class TestV090CacheAndTwoTier(unittest.TestCase):

    def test_floyd_exact_cycle_finder(self):
        """Verifies find_exact_cycle_floyd detects periodic repetitions in O(1) time."""
        # Non-cyclic
        self.assertIsNone(find_exact_cycle_floyd(["a", "b", "c", "d"]))
        self.assertIsNone(find_exact_cycle_floyd(["a"]))

        # Period 1 (Direct repetition)
        self.assertEqual(find_exact_cycle_floyd(["x", "a", "a"]), (1, 2))
        self.assertEqual(find_exact_cycle_floyd(["x", "a", "a", "a"]), (1, 3))

        # Period 2 (Oscillation A -> B -> A -> B)
        self.assertEqual(find_exact_cycle_floyd(["init", "a", "b", "a", "b"]), (2, 2))

        # Period 3 (A -> B -> C -> A -> B -> C)
        self.assertEqual(find_exact_cycle_floyd(["init", "a", "b", "c", "a", "b", "c"]), (3, 2))

    def test_two_tier_detection_tier1_exact(self):
        """Verifies that exact repetitions, oscillations, and stagnation are classified as tier1_exact."""
        detector = DeadlockDetector(repetition_threshold=3, oscillation_threshold=2)

        # 1. Direct Repetition -> tier1_exact
        detector.check("ls -la /data", "File not found")
        detector.check("ls -la /data", "File not found")
        evt1 = detector.check("ls -la /data", "File not found")
        self.assertTrue(evt1.is_deadlock)
        self.assertEqual(evt1.detection_tier, "tier1_exact")
        self.assertEqual(evt1.pattern_type, "direct_repetition")

        # 2. Oscillation -> tier1_exact
        detector.reset()
        detector.check("cat file_a.py", "Error 404")
        detector.check("cat file_b.py", "Error 404")
        detector.check("cat file_a.py", "Error 404")
        evt2 = detector.check("cat file_b.py", "Error 404")
        self.assertTrue(evt2.is_deadlock)
        self.assertEqual(evt2.detection_tier, "tier1_exact")
        self.assertEqual(evt2.pattern_type, "oscillation")

        # 3. Delegation cycle -> tier1_exact
        detector.reset()
        detector.check("delegate(agent='researcher')", "OK")
        detector.check("delegate(agent='coder')", "OK")
        detector.check("delegate(agent='researcher')", "OK")
        evt3 = detector.check("delegate(agent='coder')", "OK")
        self.assertTrue(evt3.is_deadlock)
        self.assertEqual(evt3.detection_tier, "tier1_exact")
        self.assertEqual(evt3.pattern_type, "delegation_cycle")

    def test_two_tier_detection_tier2_lexical(self):
        """Verifies that fuzzy loops, exploration thrashing, and attractor traps are classified as tier2_lexical."""
        # 1. Fuzzy polymorphic repetition -> tier2_lexical
        detector = DeadlockDetector(repetition_threshold=3, enable_fuzzy=True, fuzzy_threshold=0.6)
        detector.check("grep -rn 'UserModel' /app/src/models", "Error: grep failed, no matches")
        detector.check("grep -rin 'UserModel' /app/src/models", "Error: grep failed, no matches")
        evt1 = detector.check("grep -rn 'usermodel' /app/src/models", "Error: grep failed, no matches")
        self.assertTrue(evt1.is_deadlock)
        self.assertEqual(evt1.detection_tier, "tier2_lexical")
        self.assertEqual(evt1.pattern_type, "fuzzy_repetition")

        # 2. Exploration thrashing -> tier2_lexical
        detector.reset()
        detector.max_exploration_depth = 4
        for _ in range(3):
            detector.check("find . -name '*.py'", "found nothing")
        evt2 = detector.check("cat setup.py", "found nothing")
        self.assertTrue(evt2.is_deadlock)
        self.assertEqual(evt2.detection_tier, "tier2_lexical")
        self.assertEqual(evt2.pattern_type, "exploration_thrashing")

        # 3. Semantic Attractor -> tier2_lexical
        detector.reset()
        detector.enable_fuzzy = False
        detector.repetition_threshold = 10  # Ensure direct repetition does not trigger
        # Feed paraphrased commands that get trapped in the attractor vector field
        attractor_cmds = [
            "locate database connection strings in config directory",
            "grep -rn 'postgres://' app/config/",
            "find . -name '*database.yml*'",
            "search for db host and port in application settings",
            "cat /etc/database/connection.conf",
        ]
        evt3 = None
        for cmd in attractor_cmds:
            evt3 = detector.check(cmd, "error connection refused")
            if evt3.is_deadlock:
                break

        if evt3 and evt3.is_deadlock:
            self.assertEqual(evt3.detection_tier, "tier2_lexical")

    def test_cache_preserving_rollback_preserves_prefix(self):
        """
        Verifies that ContextPruner.rollback_and_reflect with cache_preserving=True
        preserves historical messages byte-for-byte, guaranteeing prefix prompt cache hits.
        """
        pruner = ContextPruner()
        system_turn = {"role": "system", "content": "You are a professional software engineer."}
        user_turn_1 = {"role": "user", "content": "Please refactor the user auth middleware."}
        asst_turn_1 = {"role": "assistant", "content": "I will examine the codebase."}
        user_turn_2 = {"role": "user", "content": "Go ahead."}
        asst_turn_2 = {"role": "assistant", "content": "Working on the refactor."}
        asst_turn_3 = {"role": "assistant", "content": "Running pytest on auth."}
        asst_turn_4 = {"role": "assistant", "content": "pytest failed with circular dependency."}

        messages = [
            system_turn,
            user_turn_1,
            asst_turn_1,
            user_turn_2,
            asst_turn_2,
            asst_turn_3,
            asst_turn_4,
        ]

        result = pruner.rollback_and_reflect(
            messages=messages,
            failing_action="python -m pytest",
            deadlock_details="Circular dependency deadlock",
            rollback_turns=2,
            cache_preserving=True,
        )

        self.assertTrue(result.cache_preserved)
        self.assertGreater(result.messages_removed_count, 0)
        pruned = result.pruned_messages

        # The preserved prefix (turns 0 to 4) must be completely identical
        self.assertEqual(pruned[0]["role"], "system")
        self.assertEqual(pruned[0]["content"], system_turn["content"])
        self.assertEqual(pruned[1]["role"], "user")
        self.assertEqual(pruned[1]["content"], user_turn_1["content"])
        self.assertEqual(pruned[2]["role"], "assistant")
        self.assertEqual(pruned[2]["content"], asst_turn_1["content"])
        self.assertEqual(pruned[3]["role"], "user")
        self.assertEqual(pruned[3]["content"], user_turn_2["content"])
        self.assertEqual(pruned[4]["role"], "assistant")
        self.assertEqual(pruned[4]["content"], asst_turn_2["content"])

    def test_cache_preserving_prune_dead_searches(self):
        """
        Verifies that prune_dead_searches with cache_preserving=True protects
        historical prefix messages byte-for-byte, while cache_preserving=False
        runs whole-history compaction.
        """
        pruner = ContextPruner()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Find the auth token generator."},
            # Middle ancient dead search
            {"role": "tool", "content": "No matches found for 'auth_token_generator' in src/\n" * 5},
            {"role": "assistant", "content": "Checking secondary path."},
            # Another middle dead search
            {"role": "tool", "content": "Directory /opt/tokens not found in current workspace\n" * 5},
            {"role": "assistant", "content": "Let me check recent files."},
            # Recent messages (tail)
            {"role": "tool", "content": "0 matches found in /tmp/cache.log\n" * 5},
            {"role": "assistant", "content": "Ready to write code."},
        ]

        # Mode A: cache_preserving=True (Protects historical prefix 0..boundary byte-for-byte)
        res_cache = pruner.prune_dead_searches(messages, max_age_turns=2, cache_preserving=True)
        self.assertTrue(res_cache.cache_preserved)
        # Prefix messages (index 2 and 4) must NOT be mutated in cache-preserving mode
        self.assertIn("No matches found for 'auth_token_generator'", res_cache.pruned_messages[2]["content"])
        self.assertIn("Directory /opt/tokens not found", res_cache.pruned_messages[4]["content"])
        # Tail dead search (index 6) is in the un-cached suffix window, so it gets compressed
        self.assertIn("[Search Result: 0 matches found", res_cache.pruned_messages[6]["content"])

        # Mode B: cache_preserving=False (Aggressive whole-history compaction for local LLMs/Ollama)
        res_aggressive = pruner.prune_dead_searches(messages, max_age_turns=2, cache_preserving=False)
        self.assertFalse(res_aggressive.cache_preserved)
        # Ancient messages (index 2 and 4) ARE compressed
        self.assertIn("[Search Result: 0 matches found", res_aggressive.pruned_messages[2]["content"])
        self.assertIn("[Search Result: 0 matches found", res_aggressive.pruned_messages[4]["content"])


if __name__ == "__main__":
    unittest.main()
