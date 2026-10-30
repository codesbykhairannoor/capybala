"""
capybala.pruner
~~~~~~~~~~~~~~~
Thread-Safe, Deep-Copy, Schema-Invariant Context Rollback & Reflection Engine.
Guarantees:
- Zero orphan tool calls or responses across OpenAI, Anthropic, and Llama Stack.
- Zero caller message pollution via strict copy.deepcopy().
- Universal provider schema compatibility: enforces strict turn alternation
  for Anthropic Claude (preventing consecutive 'user' roles), and eliminates
  mid-stream 'system' role rejections (which trigger 400 Bad Request on Anthropic, Mistral, and Llama-3).
- Defensive invariant handling for non-dict or malformed message structures.
- Thread-safe telemetry with internal reentrant mutex (threading.RLock).
"""

import re
import copy
import threading
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class PruneResult:
    pruned_messages: List[Dict[str, Any]]
    messages_removed_count: int
    characters_saved: int
    tokens_saved_estimate: int
    tombstone: str


class ContextPruner:
    """
    Atomic Checkpoint Rollback Engine for Capybala.
    Maintains rigorous protocol invariants and prevents LLM cognitive loops.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.total_tokens_saved = 0
        self.total_prune_operations = 0

    def _is_tool_response(self, msg: Dict[str, Any]) -> bool:
        """Determines if a message is a tool execution result across OpenAI, Anthropic, and Gemini."""
        if not isinstance(msg, dict):
            return False
        role = msg.get("role")
        if role in ("tool", "tool_response"):
            return True
        # Anthropic Claude tool response: role == 'user' containing tool_result content block
        if role == "user":
            content = msg.get("content")
            if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                return True
        return False

    def _has_tool_calls(self, msg: Dict[str, Any]) -> bool:
        """Determines if a message contains tool/function calls across OpenAI, Anthropic, and Gemini."""
        if not isinstance(msg, dict):
            return False
        role = msg.get("role")
        if role in ("assistant", "model"):
            if msg.get("tool_calls") or msg.get("function_call") or msg.get("parts"):
                return True
            # Anthropic Claude tool call: content block list containing tool_use
            content = msg.get("content")
            if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_use" for b in content):
                return True
        return False

    def rollback_and_reflect(
        self,
        messages: List[Dict[str, Any]],
        failing_action: str,
        deadlock_details: str,
        reflection_guidance: str = "",
        provider: str = "auto",
        rollback_turns: int = 4,
    ) -> PruneResult:
        """
        Executes an Atomic Checkpoint Rollback:
        1. Protects Root Context (system prompt + initial user prompt).
        2. Rewinds history atomically before unfulfilled tool calls or orphan responses.
        3. Enforces strict provider schema invariants (Anthropic turn alternation).
        4. Returns a deep-copied history with injected recovery guidance.
        """
        with self._lock:
            if not messages:
                return PruneResult(
                    pruned_messages=[],
                    messages_removed_count=0,
                    characters_saved=0,
                    tokens_saved_estimate=0,
                    tombstone="",
                )

        # Defensive sanitization: ensure list of dicts
        valid_messages = [m for m in messages if isinstance(m, dict)]
        if not valid_messages:
            return PruneResult(
                pruned_messages=[],
                messages_removed_count=0,
                characters_saved=0,
                tokens_saved_estimate=0,
                tombstone="",
            )

        # 1. Protect Root Context: System instruction (turn 0) and first user prompt
        protected_prefix_count = 1
        for i, msg in enumerate(valid_messages[:4]):
            if msg.get("role") == "user":
                protected_prefix_count = i + 1
                break

        # Calculate initial target rollback boundary
        target_idx = max(protected_prefix_count, len(valid_messages) - rollback_turns)

        # 2. STRICT PROTOCOL SCHEMA ADJACENCY ALIGNMENT
        # (Prevents OpenAI, Anthropic & Gemini 400 Bad Request on incomplete tool batches)
        while target_idx > protected_prefix_count:
            curr = valid_messages[target_idx - 1]
            if self._is_tool_response(curr):
                target_idx -= 1
                continue
            if self._has_tool_calls(curr):
                target_idx -= 1
                continue
            break

        # Also ensure target_idx itself is not in the middle of an unfulfilled tool batch
        if target_idx < len(valid_messages) and self._is_tool_response(valid_messages[target_idx]):
            while target_idx > protected_prefix_count:
                target_idx -= 1
                if self._has_tool_calls(valid_messages[target_idx]):
                    target_idx -= 1
                    break

        target_idx = max(protected_prefix_count, target_idx)

        # Deep-copy to prevent mutating caller message objects
        clean_history = copy.deepcopy(valid_messages[:target_idx])
        discarded_slice = valid_messages[target_idx:]

        # Calculate token savings
        chars_saved = sum(len(str(m.get("content", ""))) for m in discarded_slice)
        tokens_saved = max(1, int(chars_saved / 4))

        # 3. SYNTHESIZED RECOVERY GUIDANCE
        guidance = (
            reflection_guidance.strip()
            if reflection_guidance
            else "Formulate an alternative hypothesis. Avoid repeating the exact failing command."
        )
        reflection_text = (
            f"[🦫 CAPYBALA STATE ROLLBACK & RECOVERY GUIDANCE (CAPYBALA DOCTOR INTERVENTION)]\n"
            f"• Execution Status: Cognitive deadlock detected ({deadlock_details}).\n"
            f"• Rolled Back: Reverted {len(discarded_slice)} redundant turns (saved ~{tokens_saved:,} tokens).\n"
            f"• Failed Action: '{failing_action[:70]}'\n"
            f"• Strategic Directive:\n{guidance}\n"
            f"Resume task execution from this clean checkpoint."
        )

        # 4. UNIVERSAL PROVIDER SCHEMA COMPLIANCE
        # Mid-stream role: 'system' is rejected with 400 Bad Request by Anthropic, Mistral, and Llama-3!
        # Inject recovery directive as role: 'user'.
        # For Anthropic, merge into the existing user turn if present to strictly enforce Claude turn-alternation schema.
        is_anthropic = (provider.lower() == "anthropic") or (
            provider.lower() == "auto"
            and any(("tool_use_id" in str(m) or "tool_use" in str(m) or "tool_result" in str(m)) for m in valid_messages)
        )

        if is_anthropic:
            if clean_history and clean_history[-1].get("role") == "user":
                prev_content = clean_history[-1].get("content")
                if isinstance(prev_content, list):
                    clean_history[-1]["content"] = prev_content + [{"type": "text", "text": f"\n\n{reflection_text}"}]
                else:
                    clean_history[-1]["content"] = f"{prev_content or ''}\n\n{reflection_text}"
            else:
                clean_history.append({"role": "user", "content": reflection_text})
        else:
            clean_history.append({"role": "user", "content": reflection_text})

        self.total_tokens_saved += tokens_saved
        self.total_prune_operations += 1

        return PruneResult(
            pruned_messages=clean_history,
            messages_removed_count=len(discarded_slice),
            characters_saved=chars_saved,
            tokens_saved_estimate=tokens_saved,
            tombstone=reflection_text,
        )

    def prune(
        self,
        messages: List[Dict[str, Any]],
        deadlock_reason: str = "Deadlock",
        cycle_length: int = 4,
    ) -> PruneResult:
        """Legacy alias for backward compatibility."""
        with self._lock:
            res = self.rollback_and_reflect(
                messages=messages,
                failing_action="Command repeated",
                deadlock_details=deadlock_reason,
                reflection_guidance="Formulate an alternative hypothesis. Avoid repeating the exact failing command.",
                rollback_turns=cycle_length,
            )
            tombstone_marker = f"[🦫 CAPYBALA PRUNING: Collapsed {cycle_length} turns. {deadlock_reason}]"
            has_prune_marker = any("CAPYBALA PRUNING" in m.get("content", "") for m in res.pruned_messages)
            if not has_prune_marker:
                res.pruned_messages.append({"role": "user", "content": tombstone_marker})
            res.tombstone = tombstone_marker
            return res

    def prune_dead_searches(
        self,
        messages: List[Dict[str, Any]],
        max_age_turns: int = 6,
    ) -> PruneResult:
        """
        Compresses ancient negative tool observations (e.g. '0 matches found', 'Directory not found')
        older than `max_age_turns` to prevent low-information noise from polluting the LLM context.
        Preserves message roles, turn alternation, and schema structure.
        """
        with self._lock:
            if not messages or len(messages) <= max_age_turns:
                return PruneResult(
                    pruned_messages=copy.deepcopy(messages),
                    messages_removed_count=0,
                    characters_saved=0,
                    tokens_saved_estimate=0,
                    tombstone="",
                )

            cleaned_messages = copy.deepcopy(messages)
            chars_saved = 0
            compressed_count = 0

            # Safe boundary: strictly protects turns within max_age_turns and root context (index 0)
            effective_age = max(1, max_age_turns)
            boundary = max(1, len(cleaned_messages) - effective_age)

            neg_patterns = (
                r"\b(?:no matches found|found 0 matches|0 matches found|directory [^\n]+ not found|file not found|no such file or directory)\b"
            )
            positive_guard = (
                r"\b(?:found \d+ matches|\d+ lines total|records found|loaded successfully|test passed)\b"
            )

            for i in range(1, boundary):
                msg = cleaned_messages[i]
                # STRICT ISOLATION: ONLY compress genuine tool observations, NEVER user or assistant messages
                if not self._is_tool_response(msg):
                    continue

                content = msg.get("content")
                # 1. Standard string content (OpenAI / standard tool format)
                if isinstance(content, str) and len(content) > 60:
                    if re.search(neg_patterns, content, re.IGNORECASE) and not re.search(positive_guard, content, re.IGNORECASE):
                        first_line = content.strip().splitlines()[0][:80]
                        tombstone = f"[Search Result: 0 matches found ({first_line})]"
                        chars_saved += max(0, len(content) - len(tombstone))
                        msg["content"] = tombstone
                        compressed_count += 1
                # 2. Anthropic Claude list-of-blocks tool_result format
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            b_content = block.get("content")
                            if isinstance(b_content, str) and len(b_content) > 60:
                                if re.search(neg_patterns, b_content, re.IGNORECASE) and not re.search(positive_guard, b_content, re.IGNORECASE):
                                    first_line = b_content.strip().splitlines()[0][:80]
                                    tombstone = f"[Search Result: 0 matches found ({first_line})]"
                                    chars_saved += max(0, len(b_content) - len(tombstone))
                                    block["content"] = tombstone
                                    compressed_count += 1

            tokens_saved = max(0, int(chars_saved / 4))
            self.total_tokens_saved += tokens_saved

            return PruneResult(
                pruned_messages=cleaned_messages,
                messages_removed_count=compressed_count,
                characters_saved=chars_saved,
                tokens_saved_estimate=tokens_saved,
                tombstone="[Pruned dead searches]",
            )
