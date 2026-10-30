"""
capybala.detector
~~~~~~~~~~~~~~~~~
Zero-overhead, bounded-memory algorithmic detector for Cognitive Deadlocks:
- Direct action repetition (A -> A -> A)
- Fuzzy polymorphic loop detection (token Jaccard + 3-gram character shingles)
- Multi-agent delegation ping-pong cycle detection (A <-> B handoff cycles)
- Multi-step oscillation loops (A -> B -> A -> B or A -> B -> C -> A -> B -> C)
- Repeating traceback exception signatures
- Observation / output stagnation with dynamic polling exemptions
- Dynamic tool-call polling unpacker & whitelist (curl, kubectl, docker wait, ps)
- Volatile JSON argument normalizer (strips dynamic timestamps, nonces, request IDs)
- Circuit breaker engine preventing Infinite Healing Loops (Meta-Deadlocks)
- Zero memory pinning: ring buffer stores 16-byte SHA digests and compact previews.
"""

import re
import json
import hashlib
import threading
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
    pattern_type: Optional[str] = None  # 'direct_repetition', 'fuzzy_repetition', 'delegation_cycle', 'oscillation', 'semantic_traceback', 'output_stagnation'
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

# Primary read-only command verbs (arguments do NOT make them mutating)
READ_ONLY_COMMAND_VERBS = (
    "grep", "find", "cat", "head", "tail", "less", "more",
    "ls", "dir", "pwd", "cd", "echo", "env", "which", "file",
    "open", "view", "read", "search", "find_file"
)

# Mutating commands that actually alter files, system state, or run verification
MUTATING_COMMAND_VERBS = (
    "edit", "write", "create", "replace", "patch", "rm", "del",
    "mkdir", "touch", "cp", "mv", "sed", "python", "pytest",
    "unittest", "node", "npm", "yarn", "cargo", "make", "go",
    "pip", "submit"
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
        fuzzy_threshold: float = 0.65,
        enable_fuzzy: bool = True,
        enable_delegation: bool = True,
        max_exploration_depth: int = 15,
        enable_exploration_guard: bool = True,
    ):
        self.repetition_threshold = repetition_threshold
        self.oscillation_threshold = oscillation_threshold
        self.history_window = history_window
        self.max_interventions = max_interventions
        self.circuit_breaker_enabled = circuit_breaker_enabled
        self.fuzzy_threshold = fuzzy_threshold
        self.enable_fuzzy = enable_fuzzy
        self.enable_delegation = enable_delegation
        self.max_exploration_depth = max_exploration_depth
        self.enable_exploration_guard = enable_exploration_guard

        # Store ONLY compact fixed-size digests (16 bytes each), previews, and bounded buffers
        self.action_history: deque = deque(maxlen=history_window)
        self.obs_hash_history: deque = deque(maxlen=history_window)
        self.observation_signatures: deque = deque(maxlen=history_window)
        self.action_previews: deque = deque(maxlen=history_window)
        self.raw_actions: deque = deque(maxlen=history_window)
        self.full_action_sha_history: deque = deque(maxlen=history_window)
        self.delegation_history: deque = deque(maxlen=history_window)
        self.turn_counter = 0

        # Exploration thrashing tracking
        self.consecutive_exploration_turns = 0

        # Thread-safety lock
        self._lock = threading.RLock()

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

        # Replace UUIDs / GUIDs without catastrophic backtracking
        s = re.sub(r"(?:\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", "<UUID>", s)

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

    def _has_failure_indicator(self, text: Optional[str]) -> bool:
        """
        Detects genuine failure indicators while strictly ignoring false positives
        such as '0 failed', '0 errors', 'no errors', 'zero failures' common in passing test outputs.
        """
        if not text:
            return False
        clean = re.sub(
            r"\b(?:0|zero|no)\s+(?:errors?|failures?|failed|exceptions?)\b",
            "",
            str(text).lower()
        )
        return bool(re.search(r"\b(error|fail|failed|failure|exception|denied|refused|cannot|unresolved)\b", clean))

    def _calculate_fuzzy_similarity(self, s1: str, s2: str) -> float:
        """
        Calculates ultra-fast sub-millisecond lexical similarity combining
        token overlap and 3-gram character shingles (zero external dependencies).
        Bounded to first 4,096 characters to prevent ReDoS or unbounded allocation.
        """
        s1_str = str(s1 or "")[:4096]
        s2_str = str(s2 or "")[:4096]

        if s1_str == s2_str:
            return 1.0 if s1_str else 0.0

        s1_clean = re.sub(r"\s+", " ", s1_str.lower()).strip()
        s2_clean = re.sub(r"\s+", " ", s2_str.lower()).strip()

        if s1_clean == s2_clean:
            return 1.0 if s1_clean else 0.0
        if not s1_clean or not s2_clean:
            return 0.0

        tok1 = set(re.findall(r"[a-zA-Z0-9_\-\./]+", s1_clean))
        tok2 = set(re.findall(r"[a-zA-Z0-9_\-\./]+", s2_clean))

        if not tok1 and not tok2:
            jaccard_tok = 1.0 if s1_clean == s2_clean else 0.0
            overlap_tok = jaccard_tok
        else:
            jaccard_tok = len(tok1 & tok2) / len(tok1 | tok2) if (tok1 or tok2) else 0.0
            min_tok = min(len(tok1), len(tok2))
            overlap_tok = len(tok1 & tok2) / min_tok if min_tok > 0 else 0.0

        k = 3
        sh1 = {s1_clean[i:i+k] for i in range(len(s1_clean) - k + 1)} if len(s1_clean) >= k else {s1_clean}
        sh2 = {s2_clean[i:i+k] for i in range(len(s2_clean) - k + 1)} if len(s2_clean) >= k else {s2_clean}

        if not sh1 and not sh2:
            jaccard_char = 1.0 if s1_clean == s2_clean else 0.0
            overlap_char = jaccard_char
        else:
            jaccard_char = len(sh1 & sh2) / len(sh1 | sh2) if (sh1 or sh2) else 0.0
            min_char = min(len(sh1), len(sh2))
            overlap_char = len(sh1 & sh2) / min_char if min_char > 0 else 0.0

        sim = 0.35 * overlap_char + 0.25 * overlap_tok + 0.20 * jaccard_tok + 0.20 * jaccard_char
        return round(sim, 4)

    def _extract_delegation_target(self, action: Optional[str]) -> str:
        """
        Extracts target agent / recipient from multi-agent handoff primitives
        (CrewAI, LangGraph, AutoGen, OpenAI Swarm).
        Supports nested lists, JSON dicts, and tool wrappers.
        """
        if not action:
            return ""

        act_str = str(action).strip()

        # 1. JSON or dict payload containing delegation keys or lists
        dict_match = re.search(r"(\{.*\}|\[.*\])", act_str, re.DOTALL)
        if dict_match:
            try:
                data = json.loads(dict_match.group(0))
                if isinstance(data, dict):
                    for pl_key in ("targets", "recipients", "agents", "coworkers"):
                        if pl_key in data and isinstance(data[pl_key], list) and data[pl_key]:
                            return str(data[pl_key][0]).strip().lower()
                    for key in ("agent", "target", "recipient", "coworker", "target_agent", "recipient_agent", "next_agent"):
                        if key in data and data[key]:
                            val = data[key]
                            if isinstance(val, list) and val:
                                return str(val[0]).strip().lower()
                            if isinstance(val, str):
                                return val.strip().lower()
            except Exception:
                pass

        # 2. Direct tool call pattern: e.g. delegate_to(agent="coder", ...), handoff("qa")
        m = re.search(
            r"(?:delegate|handoff|transfer|assign|route|call_subagent|ask_agent)[a-zA-Z0-9_]*\s*\(\s*(?:(?:agent|target|recipient|coworker|to_agent|agent_name)\s*=\s*)?['\"]([a-zA-Z0-9_\-]+)['\"]",
            act_str,
            re.IGNORECASE
        )
        if m:
            return m.group(1).lower()

        # 3. Key-value pair in unparsed action strings: coworker='Engineer' or agent="coder"
        m_kv = re.search(
            r"['\"]?(?:agent|target|recipient|coworker|target_agent|recipient_agent|next_agent)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]+)['\"]",
            act_str,
            re.IGNORECASE
        )
        if m_kv and re.search(r"(?:delegate|handoff|transfer|assign|route|subagent|agent|ask)", act_str, re.IGNORECASE):
            return m_kv.group(1).lower()

        return ""

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

    def _is_mutating_or_execution(self, action: Optional[str]) -> bool:
        """
        Determines if an action modifies state, writes code, or executes verification.
        Inspects primary command verbs to prevent false positives on arguments
        (e.g. `grep 'write' file.py` or `find . -name '*create*'` are strictly read-only).
        """
        if not action:
            return False
        act_clean = str(action).strip().lower()

        # 1. Unpack tool call wrapper if present
        # e.g. bash({"command": "grep write ..."}) or run_shell("find ...")
        cmd_match = re.search(r"['\"](?:command|cmd|input|script)['\"]\s*:\s*['\"]([^'\"]+)['\"]", act_clean)
        if cmd_match:
            act_clean = cmd_match.group(1).strip()
        else:
            sub_match = re.search(r"^[a-zA-Z0-9_]+\s*\(\s*['\"]?(.*?)['\"]?\s*\)$", act_clean)
            if sub_match:
                act_clean = sub_match.group(1).strip()

        # Strip command prefixes like sudo, nohup, timeout
        act_clean = re.sub(r"^(?:sudo|nohup|timeout\s+\d+|watch\s+-n\s+\d+)\s+", "", act_clean).strip()

        # Check git subcommands specifically
        if act_clean.startswith("git ") or act_clean.startswith("git\t"):
            parts = act_clean.split()
            git_sub = parts[1] if len(parts) > 1 else ""
            if git_sub in ("log", "show", "status", "diff", "branch", "tag", "remote"):
                return False
            if git_sub in ("commit", "add", "checkout", "apply", "revert", "reset", "push", "pull", "merge", "stash"):
                return True
            return False

        # Extract primary command verb (first token)
        first_token = act_clean.split()[0] if act_clean else ""
        first_token = re.sub(r"[^a-zA-Z0-9_\-]", "", first_token)

        # 2. Strict read-only precedence
        for ro in READ_ONLY_COMMAND_VERBS:
            if first_token == ro or first_token.startswith(ro):
                return False

        # 3. Check mutating verbs
        for mut in MUTATING_COMMAND_VERBS:
            if first_token == mut or first_token.startswith(mut):
                return True

        # Fallback: check if line begins with an active command
        return bool(re.search(r"^(?:edit|write|create|replace|patch|rm|del|mkdir|touch|cp|mv|python|pytest|unittest|make|cargo|npm|pip|submit)\b", act_clean))

    def _is_active_code_refinement(self, recent_actions: List[str], safe_obs: str) -> bool:
        """
        Detects if the agent is actively iterating on code edits (e.g. fixing syntax errors)
        where consecutive edit payloads differ, avoiding premature false alarms on interactive editor refinement.
        Uses full-action SHA digests to guarantee 100% precision regardless of payload length.
        """
        if len(self.full_action_sha_history) < 2:
            return False
        # Check if recent action is an edit command
        is_edit_cmd = any(re.search(r"^(?:edit|patch|replace|write_file|create)\b", str(a).strip().lower()) for a in recent_actions)
        if not is_edit_cmd:
            return False
        # Check if failure is an editor syntax warning
        obs_lower = (safe_obs or "").lower()
        is_syntax_issue = any(k in obs_lower for k in ("syntax error", "syntaxerror", "invalid syntax", "unexpected indent", "new syntax error"))
        if not is_syntax_issue:
            return False
        # Check if full payload changed between the last two attempts via 16-byte SHA
        return self.full_action_sha_history[-1] != self.full_action_sha_history[-2]

    def _hash(self, text: Optional[str]) -> str:
        return hashlib.sha256(self._normalize_text(text).encode("utf-8")).hexdigest()[:16]

    def _extract_error_signature(self, output: Optional[str], action: Optional[str] = "") -> Optional[str]:
        """
        Extracts specific Exception signature along with the target error message.
        Inspects only the tail 16KB where stack traces reside.
        Strips passing summary counts ('0 failed', 'no errors') to prevent false positive matches.
        """
        if not output:
            return None

        target = str(output)[-16384:]
        # Strip passing counters so words like '0 failed' or 'no errors' are never misidentified as exceptions
        clean_target = re.sub(
            r"\b(?:0|zero|no)\s+(?:errors?|failures?|failed|exceptions?)\b",
            "",
            target,
            flags=re.IGNORECASE
        )

        error_match = re.findall(
            r"([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception|FAILED|SyntaxError|NameError|ImportError|AttributeError|IndexError|KeyError):?\s*(.*)",
            clean_target,
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
        Thread-safe under concurrent agent environments.
        """
        with self._lock:
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
            self.raw_actions.append(raw_action[:512])
            full_action_sha = hashlib.sha256(raw_action.encode("utf-8")).hexdigest()[:16]
            self.full_action_sha_history.append(full_action_sha)

            del_target = self._extract_delegation_target(raw_action)
            self.delegation_history.append(del_target)

            # 0. WHITELIST CHECK: Legitimate Polling Primitives are exempt
            if self._is_polling_command(raw_action):
                self.consecutive_exploration_turns = 0  # Legitimate polling resets exploration thrashing
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
                    has_error = any(e is not None for e in recent_errs) or self._has_failure_indicator(safe_obs)
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

            # 2. FUZZY POLYMORPHIC REPETITION CHECK (minor flag/parameter variations with failure)
            if not detected_event and self.enable_fuzzy and len(self.raw_actions) >= self.repetition_threshold:
                recent_raw = list(self.raw_actions)[-self.repetition_threshold:]
                
                # Adaptive threshold: if the agent is actively refining code following syntax warnings,
                # give 1 extra iteration of grace period to prevent false alarms on interactive editing
                is_refining = self._is_active_code_refinement(recent_raw, safe_obs)
                effective_threshold = self.repetition_threshold + 1 if is_refining else self.repetition_threshold

                if len(self.raw_actions) >= effective_threshold:
                    eval_raw = list(self.raw_actions)[-effective_threshold:]
                    eval_errs = list(self.observation_signatures)[-effective_threshold:]

                    # MUST have active error or failure indications (never flag successful variations)
                    has_error = any(e is not None for e in eval_errs) or self._has_failure_indicator(safe_obs)

                    if has_error:
                        # Check if all actions are variants of the anchor action (eval_raw[0])
                        # OR all adjacent pairs have high fuzzy similarity
                        is_anchor_loop = all(
                            self._calculate_fuzzy_similarity(eval_raw[0], eval_raw[i]) >= self.fuzzy_threshold
                            for i in range(1, len(eval_raw))
                        )
                        is_pairwise_loop = all(
                            self._calculate_fuzzy_similarity(eval_raw[i], eval_raw[i + 1]) >= self.fuzzy_threshold
                            for i in range(len(eval_raw) - 1)
                        )

                        if is_anchor_loop or is_pairwise_loop:
                            onset_turn = max(1, self.turn_counter - effective_threshold + 1)
                            preview = self.action_previews[-1] if self.action_previews else raw_action[:60]
                            detected_event = DeadlockEvent(
                                is_deadlock=True,
                                pattern_type="fuzzy_repetition",
                                repetition_count=effective_threshold,
                                details=f"Polymorphic command loop ({effective_threshold}x variants with persistent failure): '{preview}'",
                                signature=f"fuzzy_{self._hash(eval_raw[-1])}",
                                loop_onset_turn=onset_turn,
                            )

            # 3. MULTI-AGENT DELEGATION CYCLE CHECK (Agent A <-> Agent B ping-pong)
            if not detected_event and self.enable_delegation:
                valid_del = [t for t in self.delegation_history if t]
                if len(valid_del) >= 4:
                    # 2-agent ping-pong: A -> B -> A -> B
                    if valid_del[-1] == valid_del[-3] and valid_del[-2] == valid_del[-4] and valid_del[-1] != valid_del[-2]:
                        onset_turn = max(1, self.turn_counter - 4 + 1)
                        detected_event = DeadlockEvent(
                            is_deadlock=True,
                            pattern_type="delegation_cycle",
                            repetition_count=2,
                            details=f"Multi-agent delegation cycle detected: '{valid_del[-2]}' <-> '{valid_del[-1]}' ping-pong handoffs.",
                            signature=f"del_{valid_del[-2]}_{valid_del[-1]}",
                            loop_onset_turn=onset_turn,
                        )
                    # 3-agent cycle: A -> B -> C -> A -> B -> C
                    elif len(valid_del) >= 6:
                        if (
                            valid_del[-1] == valid_del[-4]
                            and valid_del[-2] == valid_del[-5]
                            and valid_del[-3] == valid_del[-6]
                            and len({valid_del[-1], valid_del[-2], valid_del[-3]}) == 3
                        ):
                            onset_turn = max(1, self.turn_counter - 6 + 1)
                            detected_event = DeadlockEvent(
                                is_deadlock=True,
                                pattern_type="delegation_cycle",
                                repetition_count=2,
                                details=f"Multi-agent delegation cycle detected: 3-agent loop ({valid_del[-3]} -> {valid_del[-2]} -> {valid_del[-1]}).",
                                signature=f"del_{valid_del[-3]}_{valid_del[-2]}_{valid_del[-1]}",
                                loop_onset_turn=onset_turn,
                            )

            # 4. OSCILLATION LOOP CHECK
            if not detected_event:
                hist = list(self.action_history)
                n = len(hist)

                # 4a. Period-2 Oscillation (A -> B -> A -> B)
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

                # 4b. Period-3 Oscillation (A -> B -> C -> A -> B -> C)
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

            # 5. SEMANTIC TRACEBACK DEADLOCK CHECK
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

            # 6. OBSERVATION STAGNATION DEADLOCK CHECK (Identical error output across turns)
            if not detected_event:
                is_refining = self._is_active_code_refinement(list(self.raw_actions)[-self.repetition_threshold:], safe_obs)
                eff_obs_thresh = self.repetition_threshold + 1 if is_refining else self.repetition_threshold

                if len(self.obs_hash_history) >= eff_obs_thresh:
                    recent_obs_hashes = list(self.obs_hash_history)[-eff_obs_thresh:]
                    if len(set(recent_obs_hashes)) == 1 and safe_obs.strip():
                        recent_errs = list(self.observation_signatures)[-eff_obs_thresh:]
                        has_error = any(e is not None for e in recent_errs) or self._has_failure_indicator(safe_obs)
                        if has_error:
                            onset_turn = max(1, self.turn_counter - eff_obs_thresh + 1)
                            detected_event = DeadlockEvent(
                                is_deadlock=True,
                                pattern_type="output_stagnation",
                                repetition_count=eff_obs_thresh,
                                details=f"Observation stagnation deadlock: Environment produced identical failing output {eff_obs_thresh} times in a row.",
                                signature=recent_obs_hashes[-1],
                                loop_onset_turn=onset_turn,
                            )

            # 7. EXPLORATION THRASHING CHECK (Excessive read-only queries without code mutation/testing)
            if self.enable_exploration_guard:
                if self._is_mutating_or_execution(raw_action):
                    self.consecutive_exploration_turns = 0
                else:
                    self.consecutive_exploration_turns += 1

                if not detected_event and self.consecutive_exploration_turns >= self.max_exploration_depth:
                    onset_turn = max(1, self.turn_counter - self.consecutive_exploration_turns + 1)
                    detected_event = DeadlockEvent(
                        is_deadlock=True,
                        pattern_type="exploration_thrashing",
                        repetition_count=self.consecutive_exploration_turns,
                        details=(
                            f"Exploration thrashing detected: Agent executed {self.consecutive_exploration_turns} "
                            f"consecutive read-only search/inspect operations without modifying code or executing verification."
                        ),
                        signature=f"thrash_{self.consecutive_exploration_turns}",
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
        with self._lock:
            self.action_history.clear()
            self.obs_hash_history.clear()
            self.observation_signatures.clear()
            self.action_previews.clear()
            self.raw_actions.clear()
            self.full_action_sha_history.clear()
            self.delegation_history.clear()
            self.turn_counter = 0
            self.consecutive_exploration_turns = 0
            self.consecutive_deadlocks = 0
            self.total_deadlocks_detected = 0
            self.healthy_turns_since_deadlock = 0
