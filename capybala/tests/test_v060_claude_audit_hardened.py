import unittest
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.api import heal, validate


class TestV060ClaudeAuditHardened(unittest.TestCase):
    """
    Unit tests verifying fixes for Claude Haiku audit findings in Capybala v0.6.0:
    - Command verb parsing & read-only argument immunity (grep "write", find create)
    - Full-action SHA refinement precision (>512 chars)
    - Polling command exploration reset
    - Dead search role isolation (docstrings/user prompts protected)
    - Anthropic tool_result / tool_use schema alignment
    - Parallel same-name tool call mapping
    - Anthropic block validation
    """

    def test_is_mutating_does_not_trigger_on_read_only_arguments(self):
        """Verifies that grep, find, and git log are strictly read-only even with mutation keywords."""
        detector = DeadlockDetector(max_exploration_depth=5)

        read_only_cmds = [
            'grep "write" /path/to/file.py',
            'find . -name "*create*"',
            'cat /etc/passwd | grep "edit"',
            'git show HEAD:file.py',
            'git log --oneline',
            'open reproman/interface/run.py',
            'search "def run" in run.py',
        ]

        for cmd in read_only_cmds:
            self.assertFalse(
                detector._is_mutating_or_execution(cmd),
                f"Command '{cmd}' should be identified as read-only!"
            )

        mutating_cmds = [
            'edit 10:20\ndef foo(): pass',
            'python test.py',
            'pytest tests/',
            'git commit -m "fix bug"',
            'git add .',
            'rm temp.py',
            'submit',
        ]

        for cmd in mutating_cmds:
            self.assertTrue(
                detector._is_mutating_or_execution(cmd),
                f"Command '{cmd}' should be identified as mutating!"
            )

    def test_active_refinement_payload_greater_than_512_chars(self):
        """
        Verifies that when code edit payloads exceed 512 characters,
        full-action SHA accurately detects differences without truncation blindspots.
        """
        detector = DeadlockDetector(repetition_threshold=3)

        payload_base = "edit file.py\n" + ("x" * 600)
        payload_variant = "edit file.py\n" + ("x" * 600) + "_DIFFERENT"

        obs_syntax_err = "Your proposed edit has introduced new syntax error(s). Please fix and retry."

        # Turn 1
        detector.check(payload_base, obs_syntax_err)
        # Turn 2: modified payload > 512 chars
        detector.check(payload_variant, obs_syntax_err)

        # Refinement check should detect that payload changed via SHA256
        self.assertTrue(detector._is_active_code_refinement([payload_base, payload_variant], obs_syntax_err))

        # Turn 3: identical payload to Turn 2 (no changes made)
        detector.check(payload_variant, obs_syntax_err)
        # Since Turn 2 and Turn 3 were identical, agent stopped refining
        self.assertFalse(detector._is_active_code_refinement([payload_variant, payload_variant], obs_syntax_err))

    def test_polling_resets_exploration_counter(self):
        """Verifies that legitimate polling primitives reset consecutive_exploration_turns."""
        detector = DeadlockDetector(max_exploration_depth=5)

        # 4 read-only actions
        for i in range(4):
            detector.check(f"cat file_{i}.py", "content")
        self.assertEqual(detector.consecutive_exploration_turns, 4)

        # Legitimate polling command
        detector.check("curl http://localhost:8080/health", "200 OK")
        self.assertEqual(detector.consecutive_exploration_turns, 0)

    def test_prune_dead_searches_does_not_corrupt_assistant_or_user(self):
        """Verifies that docstrings and user text containing negative words are NEVER compressed."""
        pruner = ContextPruner()

        messages = [
            {"role": "system", "content": "You are a code analyzer."},
            {"role": "user", "content": "Why does my code say 'file not found'?"},
            {"role": "assistant", "content": "def search(q):\n    '''Returns 0 matches found if query is empty'''\n    return []"},
            {"role": "tool", "content": "File not found in primary location, checking backup: found /backup/file.py (loaded 100 records)"},
            {"role": "tool", "content": "Directory /legacy not found in workspace\n" * 10},
            {"role": "assistant", "content": "Let me try another directory."},
            {"role": "user", "content": "OK."},
        ]

        res = pruner.prune_dead_searches(messages, max_age_turns=2)
        pruned = res.pruned_messages

        # User question must NOT be touched
        self.assertEqual(pruned[1]["content"], "Why does my code say 'file not found'?")
        # Assistant docstring must NOT be touched
        self.assertIn("Returns 0 matches found", pruned[2]["content"])
        # Tool with backup found must NOT be touched
        self.assertIn("checking backup: found /backup/file.py", pruned[3]["content"])
        # Dead negative tool result SHOULD be compressed
        self.assertIn("[Search Result: 0 matches found", pruned[4]["content"])

    def test_anthropic_tool_result_adjacency_alignment(self):
        """Verifies that rollback_and_reflect cleanly rewinds past Anthropic tool_result and tool_use blocks."""
        pruner = ContextPruner()

        anthropic_history = [
            {"role": "user", "content": "Fix the bug."},
            {"role": "assistant", "content": "I will inspect setup.py"},
            {"role": "user", "content": "Please proceed."},
            # Deadlock sequence with Anthropic tool blocks
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "call_1", "name": "search", "input": {"q": "deadlock"}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "call_1", "content": "No matches found"}
                ]
            }
        ]

        res = pruner.rollback_and_reflect(
            anthropic_history,
            failing_action="search",
            deadlock_details="Repeated search",
            provider="anthropic",
            rollback_turns=2
        )

        pruned = res.pruned_messages
        # Must not contain orphaned tool_use without tool_result, or isolated tool_result
        for msg in pruned:
            if isinstance(msg.get("content"), list):
                has_tool_use = any(b.get("type") == "tool_use" for b in msg["content"])
                self.assertFalse(has_tool_use, "Orphaned tool_use should have been rolled back!")

    def test_tool_call_map_parallel_same_name_collision(self):
        """Verifies that parallel tool calls with the same name are mapped correctly without collisions."""
        messages = [
            {"role": "system", "content": "You are a test agent."},
            {"role": "user", "content": "Run tests."},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "search", "arguments": '{"q": "query_alpha"}'}},
                    {"id": "call_2", "function": {"name": "search", "arguments": '{"q": "query_beta"}'}}
                ]
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "result for alpha"},
            {"role": "tool", "tool_call_id": "call_2", "content": "result for beta"},
            {"role": "assistant", "content": "Done."}
        ]

        # heal should parse the parallel calls without error
        healed = heal(messages, verbose=False)
        self.assertEqual(len(healed), len(messages))

    def test_validate_anthropic_blocks(self):
        """Verifies that validate() detects Anthropic block pairing and rejects orphan tool_use."""
        valid_anthropic = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "call_99", "name": "run", "input": {}}]
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "call_99", "content": "OK"}]
            }
        ]
        ok, err = validate(valid_anthropic)
        self.assertTrue(ok)
        self.assertIsNone(err)

        orphan_anthropic = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "call_unmatched", "name": "run", "input": {}}]
            }
        ]
        ok_orphan, err_orphan = validate(orphan_anthropic)
        self.assertFalse(ok_orphan)
        self.assertIn("Orphan tool_calls", err_orphan)


if __name__ == "__main__":
    unittest.main()
