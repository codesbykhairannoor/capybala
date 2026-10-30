"""
capybala.pruner
~~~~~~~~~~~~~~~
Thread-Safe, Deep-Copy, Schema-Invariant Context Rollback & Reflection Engine.
Guarantees:
- Zero orphan tool calls or responses across OpenAI, Anthropic, and Llama Stack.
- Zero caller message pollution via strict copy.deepcopy().
- Universal provider schema compatibility: eliminates mid-stream 'system' role
  rejections (which trigger 400 Bad Request on Anthropic, Mistral, and Llama-3).
- Thread-safe telemetry with internal mutex.
"""

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
        3. Returns a deep-copied history with injected recovery guidance.
        """
        if not messages:
            return PruneResult(
                pruned_messages=[],
                messages_removed_count=0,
                characters_saved=0,
                tokens_saved_estimate=0,
                tombstone="",
            )

        # 1. Protect Root Context: System instruction (turn 0) and first user prompt
        protected_prefix_count = 1
        for i, msg in enumerate(messages[:4]):
            if msg.get("role") == "user":
                protected_prefix_count = i + 1
                break

        # Calculate initial target rollback boundary
        target_idx = max(protected_prefix_count, len(messages) - rollback_turns)

        # 2. STRICT PROTOCOL SCHEMA ADJACENCY ALIGNMENT
        # (Prevents OpenAI & Anthropic 400 Bad Request on incomplete tool batches)
        while target_idx > protected_prefix_count:
            curr = messages[target_idx - 1]
            # If target ends on a tool response, rewind past all responses to find the calling assistant
            if curr.get("role") in ("tool", "tool_response"):
                target_idx -= 1
                continue
            # If target ends on an assistant message with tool_calls, rewind past that assistant
            if curr.get("role") == "assistant" and (curr.get("tool_calls") or curr.get("function_call")):
                target_idx -= 1
                continue
            break

        # Also ensure target_idx itself is not in the middle of a tool batch
        if target_idx < len(messages) and messages[target_idx].get("role") in ("tool", "tool_response"):
            while target_idx > protected_prefix_count:
                target_idx -= 1
                if messages[target_idx].get("role") == "assistant" and (messages[target_idx].get("tool_calls") or messages[target_idx].get("function_call")):
                    target_idx -= 1
                    break

        target_idx = max(protected_prefix_count, target_idx)

        # Deep-copy to prevent mutating caller message objects
        clean_history = copy.deepcopy(messages[:target_idx])
        discarded_slice = messages[target_idx:]

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
        # Inject recovery directive as role: 'user' to remain 100% compliant across all LLM inference engines.
        is_anthropic = provider.lower() == "anthropic" or (
            provider.lower() == "auto"
            and any(("tool_use_id" in str(m) or "tool_use" in str(m) or "tool_result" in str(m)) for m in messages)
        )

        if is_anthropic:
            if clean_history and clean_history[-1].get("role") == "user":
                # Merge into the existing user turn without violating Claude turn-alternation schema
                prev_content = clean_history[-1].get("content")
                if isinstance(prev_content, list):
                    clean_history[-1]["content"] = prev_content + [{"type": "text", "text": f"\n\n{reflection_text}"}]
                else:
                    clean_history[-1]["content"] = f"{prev_content or ''}\n\n{reflection_text}"
            else:
                clean_history.append({"role": "user", "content": reflection_text})
        else:
            clean_history.append({"role": "user", "content": reflection_text})

        with self._lock:
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
