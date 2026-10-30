"""
capybala.detector
~~~~~~~~~~~~~~~~~
Zero-overhead, bounded-memory algorithmic detector for Cognitive Deadlocks:
- Direct action repetition (A -> A -> A)
- Multi-step oscillation loops (A -> B -> A -> B or A -> B -> C -> A -> B -> C)
- Repeating traceback exception signatures
- Dynamic tool-call polling unpacker & whitelist (curl, kubectl, docker wait, ps)
- Volatile JSON argument normalizer (strips dynamic timestamps, nonces, request IDs)
- Circuit breaker engine preventing Infinite Healing Loops (Meta-Deadlocks)
- Zero memory pinning: ring buffer stores 16-byte SHA digests and 80-char previews.
"""

import re
import json
import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any, Dict, Set


class DeadlockEmergencyStop(RuntimeError):
    """
    Raised when an agent enters an infinite healing loop (meta-deadlock),
    exceeding the configured circuit breaker threshold.
    """
    def __init__(self, message: str, total_interventions: int, last_action: str = ""):
        super().__init__(message)
        self.total_interventions = total_interventions
        self.last_action = last_action


@dataclass
class DeadlockEvent:
    is_deadlock: bool
    pattern_type: Optional[str] = None  # 'direct_repetition', 'oscillation', 'semantic_traceback'
    repetition_count: int = 0
    details: str = ""
    signature: str = ""
    loop_onset_turn: int = 0  # Absolute turn where the loop first started
    is_circuit_broken: bool = False
    consecutive_deadlocks: int = 0


# Standard commands used for valid polling / waiting (exempt from static-output deadlock)
POLLING_COMMAND_PREFIXES = (
    "curl", "wget", "kubectl", "docker wait", "ps", "top",
    "sleep", "ping", "tail -f", "tail -n", "journalctl", "watch"
)

# Volatile keys stripped from JSON tool call arguments to prevent hash divergence
VOLATILE_JSON_KEYS: Set[str] = {
    "timestamp", "time", "ts", "nonce", "request_id", "req_id",
    "trace_id", "client_timestamp", "random_seed", "cache_bust",
    "session_id", "run_id", "datetime", "date"
}


class DeadlockDetector:
    """
    Monitors an autonomous agent's actions and tool outputs in real-time.
    Uses bounded memory buffers (storing compact hashes rather than full text)
    to eliminate heap retention leaks during long-running sessions.
    Includes a Circuit Breaker to prevent infinite healing loops.
    """

    def __init__(
        self,
        repetition_threshold: int = 3,
        oscillation_threshold: int = 2,
        history_window: int = 24,
        max_interventions: int = 5,
        circuit_breaker_enabled: bool = True,
    ):
        self.repetition_threshold = repetition_threshold
        self.oscillation_threshold = oscillation_threshold
        self.history_window = history_window
        self.max_interventions = max_interventions
        self.circuit_breaker_enabled = circuit_breaker_enabled

        # Store ONLY compact fixed-size digests (16 bytes each), not multi-MB strings
        self.action_history: deque = deque(maxlen=history_window)
        self.obs_hash_history: deque = deque(maxlen=history_window)
        self.observation_signatures: deque = deque(maxlen=history_window)
        self.action_previews: deque = deque(maxlen=history_window)
        self.turn_counter = 0

        # Circuit breaker state
        self.consecutive_deadlocks = 0
        self.total_deadlocks_detected = 0
        self.healthy_turns_since_deadlock = 0

    def _strip_volatile_keys(self, obj: Any) -> Any:
        """Recursively strips dynamic nonces, timestamps, and request IDs from dictionaries/lists."""
        if isinstance(obj, dict):
            return {
                k: self._strip_volatile_keys(v)
                for k, v in obj.items()
                if str(k).lower() not in VOLATILE_JSON_KEYS
            }
        elif isinstance(obj, list):
            return [self._strip_volatile_keys(item) for item in obj]
        return obj

    def _sanitize_action(self, action: Optional[str]) -> str:
        """
        Unpacks and canonicalizes tool action representations:
        1. Identifies embedded JSON or Python dict payloads in tool calls.
        2. Strips volatile keys (timestamps, nonces) so semantic repetitions match.
        3. Sorts JSON keys deterministically.
        """
        if not action:
            return ""

        act_str = str(action).strip()

        # Check for JSON/dict payload inside function call: tool_name({"cmd": "...", "ts": 123})
        dict_match = re.search(r"(\{.*\}|\[.*\])", act_str, re.DOTALL)
        if dict_match:
            raw_payload = dict_match.group(0)
            try:
                parsed = json.loads(raw_payload)
                cleaned = self._strip_volatile_keys(parsed)
                canonical = json.dumps(cleaned, sort_keys=True, separators=(',', ':'))
                act_str = act_str[:dict_match.start()] + canonical + act_str[dict_match.end():]
            except Exception:
                # If not strict JSON, try key-value regex cleanup for python dict syntax
                for v_key in VOLATILE_JSON_KEYS:
                    act_str = re.sub(rf"['\"]?{v_key}['\"]?\s*:\s*['\"]?[^,'\"}}]+['\"]?,?", "", act_str)

        return act_str

    def _normalize_text(self, text: Optional[str]) -> str:
        """
        Strips volatile dynamic noise safely:
        - Memory pointer addresses (0x7fff...) -> preserves short Git commit hashes!
        - UUIDs / GUIDs (lowercase, uppercase, or braced)
        - Floating timestamps / dates (ISO8601 with ms & tz offsets, Unix epoch timestamps)
        - Traceback line numbers (File '...', line 42) -> preserves sed/cat pagination ranges!
        - Temp directory random prefixes (POSIX /tmp and Windows AppData/Local/Temp)
        Bounded to first 32,768 characters to prevent GC heap churn and ReDoS attacks.
        """
        if not text:
            return ""

        s = str(text)[:32768].strip().lower()
        s = re.sub(r"\s+", " ", s)

        # Strip true memory pointer addresses (0x followed by 8+ hex chars) -> PRESERVES Git SHAs
        s = re.sub(r"0x[0-9a-f]{8,}", "<PTR_ADDR>", s)

        # Replace UUIDs / GUIDs
        s = re.sub(r"\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}?", "<UUID>", s)

        # Replace ISO8601 timestamps (with optional ms and timezone offsets e.g. +07:00, Z)
        s = re.sub(r"\d{4}-\d{2}-\d{2}[tT ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:z|[+-]\d{2}:?\d{2})?", "<TIMESTAMP>", s)

        # Replace Unix epoch timestamps (10 to 13 digits)
        s = re.sub(r"\b1[6789]\d{8,11}\b", "<EPOCH_TS>", s)

        # ONLY replace traceback line markers, DO NOT destroy sed/pagination ranges
        s = re.sub(r"(file\s+['\"][^'\"]+['\"],\s+line)\s+\d+", r"\1 <NUM>", s)

        # Replace temp directories (POSIX /tmp and Windows temp paths)
        s = re.sub(
            r"(?:[a-z]:[/\\](?:users[/\\][^/\\]+[/\\]appdata[/\\]local[/\\]temp|windows[/\\]temp)|(?:^|[/\\])(?:tmp|var/tmp|\.tmp|temp))[/\\][\w\d._-]+",
            "<TMP_PATH>",
            s
        )

        return s

    def _is_polling_command(self, action: Optional[str]) -> bool:
        """
        Determines if a command is a legitimate polling primitive.
        Unpacks tool wrappers like bash({'command': 'curl ...'}) or execute(cmd='kubectl ...').
        """
        if not action:
            return False

        act_clean = str(action).strip().lower()

        # Unpack tool arguments if wrapped in tool-call syntax: e.g. bash({"command": "curl ..."})
        cmd_match = re.search(r"['\"](?:command|cmd|input|script)['\"]\s*:\s*['\"]([^'\"]+)['\"]", act_clean)
        if cmd_match:
            act_clean = cmd_match.group(1).strip()
        else:
            # Also handle simple wrapper: bash(curl ...) or run_shell("curl ...")
            sub_match = re.search(r"^[a-zA-Z0-9_]+\s*\(\s*['\"]?(.*?)['\"]?\s*\)$", act_clean)
            if sub_match:
                act_clean = sub_match.group(1).strip()

        # Strip command prefixes (sudo, nohup, timeout 10)
        act_clean = re.sub(r"^(?:sudo|nohup|timeout\s+\d+|watch\s+-n\s+\d+)\s+", "", act_clean).strip()

        for prefix in POLLING_COMMAND_PREFIXES:
            p = prefix.strip()
            if act_clean == p or act_clean.startswith(p + " ") or act_clean.startswith(p + "\t"):
                return True

        return False

    def _hash(self, text: Optional[str]) -> str:
        return hashlib.sha256(self._normalize_text(text).encode("utf-8")).hexdigest()[:16]

    def _extract_error_signature(self, output: Optional[str], action: Optional[str] = "") -> Optional[str]:
        """
        Extracts specific Exception signature along with the target error message.
        Inspects only the tail 16KB where stack traces reside.
        """
        if not output:
            return None

        target = str(output)[-16384:]
        error_match = re.findall(
            r"([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception|FAILED|SyntaxError|NameError|ImportError|AttributeError|IndexError|KeyError):?\s*(.*)",
            target,
            re.IGNORECASE,
        )
        if error_match:
            last_err_name, last_err_msg = error_match[-1]
            clean_msg = self._normalize_text(last_err_msg)
            return f"{last_err_name}:{clean_msg[:80]}"

        if "traceback (most recent call last)" in target.lower():
            lines = [line.strip() for line in target.strip().splitlines() if line.strip()]
            if lines:
                return f"Traceback:{self._normalize_text(lines[-1])[:80]}"

        return None

    def check(self, current_action: Optional[str], observation: Optional[str] = "") -> DeadlockEvent:
        """
        Analyzes the latest action and environment feedback.
        Stores compact digests only, preventing memory leaks on multi-megabyte payloads.
        Sanitizes dynamic volatile keys from JSON tool arguments.
        Enforces Circuit Breaker against infinite healing loops.
        """
        self.turn_counter += 1
        raw_action = str(current_action or "")
        sanitized_action = self._sanitize_action(raw_action)
        safe_obs = str(observation or "")

        action_hash = self._hash(sanitized_action)
        obs_hash = self._hash(safe_obs)
        err_sig = self._extract_error_signature(safe_obs, sanitized_action)

        self.action_history.append(action_hash)
        self.obs_hash_history.append(obs_hash)
        self.observation_signatures.append(err_sig)
        self.action_previews.append(raw_action[:80])

        # 0. WHITELIST CHECK: Legitimate Polling Primitives are exempt
        if self._is_polling_command(raw_action):
            self.healthy_turns_since_deadlock += 1
            if self.healthy_turns_since_deadlock >= 3:
                self.consecutive_deadlocks = 0
            return DeadlockEvent(is_deadlock=False)

        detected_event: Optional[DeadlockEvent] = None

        # 1. DIRECT REPETITION CHECK (A -> A -> A)
        if len(self.action_history) >= self.repetition_threshold:
            recent_actions = list(self.action_history)[-self.repetition_threshold:]
            if len(set(recent_actions)) == 1:
                recent_errs = list(self.observation_signatures)[-self.repetition_threshold:]
                recent_obs_hashes = list(self.obs_hash_history)[-self.repetition_threshold:]

                # Require BOTH error persistence OR strictly static output across turns
                has_error = any(e is not None for e in recent_errs)
                is_stuck_output = len(set(recent_obs_hashes)) == 1

                if has_error or is_stuck_output:
                    onset_turn = max(1, self.turn_counter - self.repetition_threshold + 1)
                    preview = self.action_previews[-1] if self.action_previews else raw_action[:60]
                    detected_event = DeadlockEvent(
                        is_deadlock=True,
                        pattern_type="direct_repetition",
                        repetition_count=self.repetition_threshold,
                        details=f"Command repeated {self.repetition_threshold}x with persistent failure: '{preview}'",
                        signature=action_hash,
                        loop_onset_turn=onset_turn,
                    )

        # 2. OSCILLATION LOOP CHECK
        if not detected_event:
            hist = list(self.action_history)
            n = len(hist)

            # 2a. Period-2 Oscillation (A -> B -> A -> B)
            required_turns_p2 = self.oscillation_threshold * 2
            if n >= required_turns_p2:
                if hist[-1] == hist[-3] and hist[-2] == hist[-4] and hist[-1] != hist[-2]:
                    onset_turn = max(1, self.turn_counter - required_turns_p2 + 1)
                    detected_event = DeadlockEvent(
                        is_deadlock=True,
                        pattern_type="oscillation",
                        repetition_count=self.oscillation_threshold,
                        details=f"2-step oscillating action loop detected ({self.oscillation_threshold} cycles).",
                        signature=f"{hist[-2]}_{hist[-1]}",
                        loop_onset_turn=onset_turn,
                    )

            # 2b. Period-3 Oscillation (A -> B -> C -> A -> B -> C)
            if not detected_event:
                required_turns_p3 = 6
                if n >= required_turns_p3:
                    if (
                        hist[-1] == hist[-4]
                        and hist[-2] == hist[-5]
                        and hist[-3] == hist[-6]
                        and len({hist[-1], hist[-2], hist[-3]}) == 3
                    ):
                        onset_turn = max(1, self.turn_counter - required_turns_p3 + 1)
                        detected_event = DeadlockEvent(
                            is_deadlock=True,
                            pattern_type="oscillation",
                            repetition_count=2,
                            details="3-step oscillating action loop detected (2 cycles: A -> B -> C -> A -> B -> C).",
                            signature=f"{hist[-3]}_{hist[-2]}_{hist[-1]}",
                            loop_onset_turn=onset_turn,
                        )

        # 3. SEMANTIC TRACEBACK DEADLOCK CHECK
        if not detected_event and err_sig is not None:
            if len(self.observation_signatures) >= self.repetition_threshold:
                recent_sigs = list(self.observation_signatures)[-self.repetition_threshold:]
                if all(s == err_sig for s in recent_sigs):
                    onset_turn = max(1, self.turn_counter - self.repetition_threshold + 1)
                    detected_event = DeadlockEvent(
                        is_deadlock=True,
                        pattern_type="semantic_traceback",
                        repetition_count=self.repetition_threshold,
                        details=f"Persistent traceback deadlock: '{err_sig}' repeated {self.repetition_threshold} times.",
                        signature=self._hash(err_sig),
                        loop_onset_turn=onset_turn,
                    )

        # CIRCUIT BREAKER & PROGRESSION EVALUATION
        if detected_event and detected_event.is_deadlock:
            self.consecutive_deadlocks += 1
            self.total_deadlocks_detected += 1
            self.healthy_turns_since_deadlock = 0
            detected_event.consecutive_deadlocks = self.consecutive_deadlocks

            if self.circuit_breaker_enabled and self.consecutive_deadlocks >= self.max_interventions:
                detected_event.is_circuit_broken = True
                detected_event.details = (
                    f"CIRCUIT BREAKER TRIPPED: Exceeded max consecutive deadlock interventions "
                    f"({self.max_interventions}). Halting execution to prevent infinite token burn."
                )
            return detected_event
        else:
            # Healthy turn progression
            self.healthy_turns_since_deadlock += 1
            if self.healthy_turns_since_deadlock >= 3:
                self.consecutive_deadlocks = 0
            return DeadlockEvent(is_deadlock=False)

    def reset(self):
        """Resets detection history and circuit breaker counters."""
        self.action_history.clear()
        self.obs_hash_history.clear()
        self.observation_signatures.clear()
        self.action_previews.clear()
        self.turn_counter = 0
        self.consecutive_deadlocks = 0
        self.total_deadlocks_detected = 0
        self.healthy_turns_since_deadlock = 0
