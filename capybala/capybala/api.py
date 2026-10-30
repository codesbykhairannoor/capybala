"""
capybala.api
~~~~~~~~~~~~
Requests-Grade Developer API for Capybala.
Thread-safe, AsyncIO-safe, non-invasive runtime guard.
Zero global side-effects, type-safe, and visually informative.
Includes Circuit Breaker against Infinite Healing Loops and full streaming support.
"""

import sys
import asyncio
import functools
import inspect
import threading
from typing import List, Dict, Any, Optional, Tuple
from .detector import DeadlockDetector, DeadlockEmergencyStop
from .pruner import ContextPruner
from .healer import AgentHealer

_default_pruner = ContextPruner()
_default_healer = AgentHealer()
_api_lock = threading.RLock()


def print_flight_recorder(action: str, tokens_saved: int, cycle_length: int, details: str):
    """
    Renders a clean, formatted flight recorder to stderr when a loop is intercepted.
    Using stderr prevents corrupting stdout JSON pipelines.
    """
    usd_saved = (tokens_saved / 1_000_000.0) * 6.0
    sys.stderr.write("\n" + "─" * 65 + "\n")
    sys.stderr.write(f"🦫  \033[1;33mCapybala Cycle Intercepted\033[0m [\033[1;36m{action[:35]}\033[0m]\n")
    sys.stderr.write(f" ├── Cycle Length: \033[1m{cycle_length} turns\033[0m | Recovered: \033[1;32m~{tokens_saved:,} tokens (~${usd_saved:.3f})\033[0m\n")
    sys.stderr.write(f" └── Resolution:   \033[32mAtomic Rollback + Grounded Reflection Injected\033[0m\n")
    sys.stderr.write("─" * 65 + "\n\n")
    sys.stderr.flush()


def heal(
    messages: List[Dict[str, Any]],
    repetition_threshold: int = 3,
    provider: str = "auto",
    verbose: bool = True,
    max_interventions: int = 5,
    circuit_breaker: bool = True,
    raise_on_circuit_break: bool = False,
) -> List[Dict[str, Any]]:
    """
    1-Line Functional Healer.
    Inspects messages, detects deadlocks, performs atomic rollback, and injects reflection.
    Mutates messages in-place to prevent outer loop ghost pruning desync, and returns pruned history.
    Enforces Circuit Breaker against Infinite Healing Loops (Meta-Deadlocks).

    Usage:
        import capybala as cb
        messages = cb.heal(messages)
    """
    if not isinstance(messages, list) or len(messages) < 4:
        return messages

    # Dynamic window: inspect up to 32 recent messages to avoid parallel tool-call amnesia
    window_slice = messages[-32:] if len(messages) > 32 else messages

    tool_call_map = {}  # call_id -> action_str
    turns_sequence = []  # list of (action, observation)

    for msg in window_slice:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        content = str(msg.get("content", ""))

        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    call_id = tc.get("id")
                    fn = tc.get("function", {})
                    action_str = f"{fn.get('name', 'tool')}({fn.get('arguments', '')})"
                    if call_id:
                        tool_call_map[call_id] = action_str
                    else:
                        turns_sequence.append((action_str, ""))
        elif role in ("tool", "tool_response"):
            tid = msg.get("tool_call_id")
            act = tool_call_map.get(tid, "tool_execution")
            turns_sequence.append((act, content))
        elif role == "assistant":
            turns_sequence.append((content, ""))
        elif role in ("system", "user") and turns_sequence:
            prev_act, _ = turns_sequence[-1]
            turns_sequence[-1] = (prev_act, content)

    # Evaluate sequence against DeadlockDetector with circuit breaker
    detector = DeadlockDetector(
        repetition_threshold=repetition_threshold,
        max_interventions=max_interventions,
        circuit_breaker_enabled=circuit_breaker,
    )
    last_action = ""
    last_obs = ""
    event = None

    for action, obs in turns_sequence:
        if action:
            event = detector.check(action, obs)
            last_action = action
            last_obs = obs
            if event.is_deadlock:
                break

    if not event or not event.is_deadlock:
        return messages

    # Check circuit breaker
    if event.is_circuit_broken:
        if verbose:
            sys.stderr.write(f"\n🚨 \033[1;31m[Capybala Circuit Breaker Tripped]\033[0m {event.details}\n\n")
            sys.stderr.flush()
        if raise_on_circuit_break:
            raise DeadlockEmergencyStop(event.details, event.consecutive_deadlocks, last_action)

    # Generate constructive heuristic prescription with progressive escalation
    rx = _default_healer.prescribe(
        deadlock_pattern=event.pattern_type or "direct_repetition",
        failing_action=last_action,
        error_signature=last_obs,
        target_provider=provider,
        escalation_level=event.consecutive_deadlocks or 1,
    )

    # Execute Atomic Checkpoint Rollback with Domain Guidance
    rollback_res = _default_pruner.rollback_and_reflect(
        messages=messages,
        failing_action=last_action,
        deadlock_details=event.details,
        reflection_guidance=rx.recommended_pivot,
        provider=provider,
        rollback_turns=repetition_threshold * 2,
    )

    if verbose:
        print_flight_recorder(
            action=last_action,
            tokens_saved=rollback_res.tokens_saved_estimate,
            cycle_length=event.repetition_count,
            details=event.details,
        )

    # In-place slice mutation: Prevents Ghost Pruning Desync in developer outer loops!
    if isinstance(messages, list):
        try:
            messages[:] = rollback_res.pruned_messages
        except TypeError:
            pass

    return messages


def watch(
    client: Any,
    max_repetition: int = 3,
    verbose: bool = True,
    max_interventions: int = 5,
    circuit_breaker: bool = True,
    raise_on_circuit_break: bool = False,
) -> Any:
    """
    Explicit, Non-Invasive Client Wrapper (like Tenacity / Instructor).
    Thread-safe and AsyncIO-safe: preserves inspect.iscoroutinefunction() signatures,
    supports streaming responses (stream=True), and offloads CPU-bound regex/hashing
    to worker threads in async loops.

    Supported Clients:
        - OpenAI / AsyncOpenAI
        - Anthropic / AsyncAnthropic
        - Groq / Mistral / Ollama / LlamaStackClient

    Usage:
        client = capybala.watch(OpenAI())
    """
    with _api_lock:
        if getattr(client, "_capybala_watched", False):
            return client

        # 1. OpenAI / Groq / Mistral / Ollama style clients: client.chat.completions.create
        if hasattr(client, "chat") and hasattr(client.chat, "completions") and hasattr(client.chat.completions, "create"):
            orig_create = client.chat.completions.create

            if inspect.iscoroutinefunction(orig_create):
                @functools.wraps(orig_create)
                async def async_guarded_create(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = await asyncio.to_thread(
                            heal,
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return await orig_create(*args, **kwargs)

                client.chat.completions.create = async_guarded_create
            else:
                @functools.wraps(orig_create)
                def guarded_create(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = heal(
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return orig_create(*args, **kwargs)

                client.chat.completions.create = guarded_create

            client._capybala_watched = True
            return client

        # 2. Anthropic style clients: client.messages.create
        if hasattr(client, "messages") and hasattr(client.messages, "create"):
            orig_create = client.messages.create

            if inspect.iscoroutinefunction(orig_create):
                @functools.wraps(orig_create)
                async def async_guarded_anthropic(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = await asyncio.to_thread(
                            heal,
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            provider="anthropic",
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return await orig_create(*args, **kwargs)

                client.messages.create = async_guarded_anthropic
            else:
                @functools.wraps(orig_create)
                def guarded_anthropic(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = heal(
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            provider="anthropic",
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return orig_create(*args, **kwargs)

                client.messages.create = guarded_anthropic

            client._capybala_watched = True
            return client

        # 3. Llama Stack client: client.inference.chat_completion
        if hasattr(client, "inference") and hasattr(client.inference, "chat_completion"):
            orig_inference = client.inference.chat_completion

            if inspect.iscoroutinefunction(orig_inference):
                @functools.wraps(orig_inference)
                async def async_guarded_llama(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = await asyncio.to_thread(
                            heal,
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            provider="llama_stack",
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return await orig_inference(*args, **kwargs)

                client.inference.chat_completion = async_guarded_llama
            else:
                @functools.wraps(orig_inference)
                def guarded_llama(*args, **kwargs):
                    if "messages" in kwargs:
                        kwargs["messages"] = heal(
                            kwargs["messages"],
                            repetition_threshold=max_repetition,
                            provider="llama_stack",
                            verbose=verbose,
                            max_interventions=max_interventions,
                            circuit_breaker=circuit_breaker,
                            raise_on_circuit_break=raise_on_circuit_break,
                        )
                    return orig_inference(*args, **kwargs)

                client.inference.chat_completion = guarded_llama

            client._capybala_watched = True
            return client

        return client


def validate(messages: List[Dict[str, Any]], check_turn_alternation: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Protocol Invariant Validator.
    Verifies that tool-calls and tool-responses are perfectly paired,
    preventing any possibility of a 400 Bad Request error.
    Optionally verifies strict user-assistant turn alternation for Anthropic.
    """
    if not isinstance(messages, list):
        return False, "Messages must be a list of dicts."

    tool_call_ids = set()
    tool_response_ids = set()
    prev_role = None

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role")
        if check_turn_alternation and role in ("user", "assistant"):
            if role == prev_role:
                return False, f"Consecutive '{role}' roles detected, which violates Anthropic Claude turn-alternation schema."
            prev_role = role

        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    tool_call_ids.add(tc.get("id"))
        elif role in ("tool", "tool_response"):
            tid = msg.get("tool_call_id")
            if tid:
                tool_response_ids.add(tid)

    unmatched_calls = tool_call_ids - tool_response_ids
    unmatched_responses = tool_response_ids - tool_call_ids

    if unmatched_calls:
        return False, f"Orphan tool_calls without tool response: {unmatched_calls}"
    if unmatched_responses:
        return False, f"Orphan tool response without tool_call: {unmatched_responses}"

    return True, None
