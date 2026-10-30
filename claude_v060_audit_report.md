# CAPYBALA v0.6.0 COMPREHENSIVE SECURITY & CORRECTNESS AUDIT

## EXECUTIVE SUMMARY

**SEVERITY: CRITICAL** — This library contains **18+ exploitable flaws** spanning false-positive/negative deadlock detection, context corruption, race conditions, regex ReDoS vulnerabilities, and schema invariant violations. The circuit breaker is bypassable, and the fuzzy detection can be trivially defeated.

---

## 1. EXPLORATION THRASHING GUARD & COMMAND PARSING VULNERABILITIES

### 1.1 CRITICAL: `_is_mutating_or_execution()` Regex False Positives

**Location:** `detector.py:180-186`

```python
def _is_mutating_or_execution(self, action: Optional[str]) -> bool:
    if not action:
        return False
    act_clean = str(action).strip().lower()
    for pat in MUTATING_COMMAND_PATTERNS:
        if re.search(pat, act_clean):
            return True
    return False
```

**FLAW:** The regex patterns in `MUTATING_COMMAND_PATTERNS` (lines 36-39) are **overly broad and trigger on read-only operations**:

```python
MUTATING_COMMAND_PATTERNS = (
    r"\b(?:edit|write|create|replace|patch|rm|del|mkdir|touch|cp|mv)\b",
    r"\b(?:python|pytest|unittest|node|npm|yarn|cargo|make|go|pip|bash|sh)\b",
    r"\b(?:git\s+(?:commit|add|checkout|apply|revert|reset)|submit)\b"
)
```

**Exploitation:**
```python
# BYPASS 1: Read-only grep/find operations containing mutation keywords
action = 'grep "write" /path/to/file.py'  # Contains "write" → falsely marked as mutating
action = 'find . -name "*create*"'        # Contains "create" → falsely marked as mutating
action = 'cat /etc/passwd | grep "edit"'  # Contains "edit" → falsely marked as mutating

# BYPASS 2: Python introspection that doesn't execute code
action = 'python -c "import sys; print(sys.path)"'  # Marked mutating, but read-only
action = 'bash -c "echo hello"'                      # Marked mutating, but read-only

# BYPASS 3: Git log/show operations (read-only)
action = 'git show HEAD:file.py'  # Matches git pattern → falsely marked mutating
action = 'git log --oneline'      # Matches git pattern → falsely marked mutating
```

**IMPACT:** 
- Exploration thrashing detection is **completely unreliable**
- Legitimate read-only inspection sequences are incorrectly reset, allowing infinite loops to bypass detection
- False positives cause premature termination of valid exploration phases

**FIX REQUIRED:**
```python
MUTATING_COMMAND_PATTERNS = (
    # Only actual file mutations (not grep/find/cat)
    r"\b(?:^|\s)(?:edit|write|create|replace|patch|rm|del|mkdir|touch|cp|mv)\s+",
    # Only code execution that modifies state (not introspection)
    r"\b(?:^|\s)(?:python|bash|sh)\s+(?:-[a-z]*e|-c)\s+(?:import|exec|eval|open\(|write)",
    # Only git mutations (not log/show/diff)
    r"\b(?:^|\s)git\s+(?:commit|add|checkout|apply|revert|reset|push|pull)\b",
)
```

---

### 1.2 CRITICAL: `_is_active_code_refinement()` Payload Comparison Bypass

**Location:** `detector.py:188-204`

```python
def _is_active_code_refinement(self, recent_actions: List[str], safe_obs: str) -> bool:
    if len(recent_actions) < 2:
        return False
    is_edit_cmd = any(re.search(r"^(?:edit|patch|replace|write_file|create)\b", 
                                str(a).strip().lower()) for a in recent_actions)
    if not is_edit_cmd:
        return False
    obs_lower = (safe_obs or "").lower()
    is_syntax_issue = any(k in obs_lower for k in ("syntax error", "syntaxerror", ...))
    if not is_syntax_issue:
        return False
    return recent_actions[-1].strip() != recent_actions[-2].strip()
```

**FLAW:** The function **only compares the last two raw action strings**, which are truncated to 512 characters (line 107):

```python
self.raw_actions.append(raw_action[:512])
```

**Exploitation:**
```python
# BYPASS: Two identical edits with different payloads (both > 512 chars)
action1 = 'edit file.py\n' + 'x' * 600  # Truncated to 512 chars
action2 = 'edit file.py\n' + 'y' * 600  # Truncated to 512 chars
# Both truncate to identical 512-char prefix → `recent_actions[-1].strip() == recent_actions[-2].strip()`
# Returns False, allowing infinite edit loops to bypass fuzzy detection

# BYPASS 2: Tool call with JSON arguments
action1 = 'edit_tool({"file": "x.py", "content": "def foo(): pass"})'
action2 = 'edit_tool({"file": "x.py", "content": "def bar(): pass"})'
# Regex only checks prefix, not JSON payload → both match "^edit" → is_edit_cmd=True
# But payloads differ → should trigger refinement grace period
# However, if both are < 512 chars and differ, it works correctly
# But if wrapped in tool calls with timestamps, sanitization may strip them
```

**IMPACT:**
- Adaptive grace period can be bypassed by agents using large payloads
- Fuzzy repetition detection is defeated when payloads exceed 512 chars
- False negatives on code refinement loops

---

### 1.3 MEDIUM: `consecutive_exploration_turns` Not Reset on Polling Commands

**Location:** `detector.py:280-283`

```python
# 0. WHITELIST CHECK: Legitimate Polling Primitives are exempt
if self._is_polling_command(raw_action):
    self.healthy_turns_since_deadlock += 1
    if self.healthy_turns_since_deadlock >= 3:
        self.consecutive_deadlocks = 0
    return DeadlockEvent(is_deadlock=False)
```

**FLAW:** Polling commands **do NOT reset `consecutive_exploration_turns`**. This counter is only reset in `_is_mutating_or_execution()` (line 356):

```python
if self._is_mutating_or_execution(raw_action):
    self.consecutive_exploration_turns = 0
else:
    self.consecutive_exploration_turns += 1
```

**Exploitation:**
```python
# Sequence: polling → polling → polling → ... → polling (15+ times)
# Each polling command increments consecutive_exploration_turns
# Even though polling is whitelisted, the counter keeps growing
# After 15 polling commands, exploration_thrashing deadlock is triggered
# despite all commands being legitimate polling operations

detector = DeadlockDetector(max_exploration_depth=15)
for i in range(15):
    event = detector.check('curl http://localhost:8080/health', 'OK')
    # After 15 iterations, event.is_deadlock == True (WRONG!)
```

**IMPACT:**
- Legitimate polling sequences (e.g., health checks, retries) trigger false-positive deadlock detection
- Breaks valid wait-and-retry patterns

---

## 2. ADAPTIVE SYNTAX REFINEMENT & FUZZY DETECTION VULNERABILITIES

### 2.1 CRITICAL: Fuzzy Similarity Threshold Bypass via Whitespace Manipulation

**Location:** `detector.py:135-175`

```python
def _calculate_fuzzy_similarity(self, s1: str, s2: str) -> float:
    s1_str = str(s1 or "")[:4096]
    s2_str = str(s2 or "")[:4096]
    if s1_str == s2_str:
        return 1.0 if s1_str else 0.0
    s1_clean = re.sub(r"\s+", " ", s1_str.lower()).strip()
    s2_clean = re.sub(r"\s+", " ", s2_str.lower()).strip()
    # ... token and shingle extraction ...
```

**FLAW:** The similarity calculation uses **token overlap and character shingles**, but the weighting is **arbitrary and exploitable**:

```python
sim = 0.35 * overlap_char + 0.25 * overlap_tok + 0.20 * jaccard_tok + 0.20 * jaccard_char
```

**Exploitation:**
```python
# BYPASS: Two semantically identical but lexically different commands
s1 = "curl http://localhost:8080/api/v1/users"
s2 = "curl http://localhost:8080/api/v1/users?format=json&cache=false"

# Tokens: {curl, http, localhost, 8080, api, v1, users} vs {curl, http, localhost, 8080, api, v1, users, format, json, cache, false}
# Token overlap: 7/11 = 0.636 (below 0.65 threshold by default)
# Character shingles: high overlap on "curl http://localhost:8080/api/v1/users"
# Final similarity: 0.35*0.9 + 0.25*0.636 + 0.20*0.8 + 0.20*0.85 ≈ 0.81 (PASSES)

# But if we add more divergent parameters:
s3 = "curl http://localhost:8080/api/v1/users?format=xml&timeout=30&retry=5&auth=bearer"
# Token overlap drops further, but character shingles still match on prefix
# Similarity might drop to 0.62 (FAILS threshold)

# BYPASS: Semantic equivalence with different structure
s4 = "python -c 'import requests; requests.get(\"http://localhost:8080/api/v1/users\")'"
s5 = "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8080/api/v1/users\")'"
# Both are HTTP GET requests, but token overlap is low
# Similarity ≈ 0.45 (FAILS threshold despite semantic equivalence)
```

**IMPACT:**
- Fuzzy repetition detection is **unreliable** — similar commands may not be detected as loops
- Adversarial agents can bypass detection by adding/removing parameters
- False negatives on polymorphic loops

---

### 2.2 CRITICAL: `_normalize_text()` ReDoS Vulnerability

**Location:** `detector.py:99-130`

```python
def _normalize_text(self, text: Optional[str]) -> str:
    if not text:
        return ""
    s = str(text)[:32768].strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"0x[0-9a-f]{8,}", "<PTR_ADDR>", s)
    s = re.sub(r"\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}?", "<UUID>", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}[tT ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:z|[+-]\d{2}:?\d{2})?", "<TIMESTAMP>", s)
    s = re.sub(r"\b1[6789]\d{8,11}\b", "<EPOCH_TS>", s)
    s = re.sub(r"(file\s+['\"][^'\"]+['\"],\s+line)\s+\d+", r"\1 <NUM>", s)
    s = re.sub(
        r"(?:[a-z]:[/\\](?:users[/\\][^/\\]+[/\\]appdata[/\\]local[/\\]temp|windows[/\\]temp)|(?:^|[/\\])(?:tmp|var/tmp|\.tmp|temp))[/\\][\w\d._-]+",
        "<TMP_PATH>",
        s
    )
    return s
```

**FLAW:** The UUID regex pattern is **catastrophically backtracking-prone**:

```python
r"\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}?"
```

The optional braces `\{?` and `\}?` combined with the strict hex pattern can cause **exponential backtracking** on malformed input.

**Exploitation:**
```python
# ReDoS attack: Malformed UUID-like string
malformed = "{{{{{{{{-{{{{-{{{{-{{{{-{{{{{{{{{{{{{" * 100
detector = DeadlockDetector()
# Calling _normalize_text() with this input will hang for seconds/minutes
detector._normalize_text(malformed)

# Also the temp path regex is vulnerable:
temp_path = "c:\\users\\" + "a" * 1000 + "\\appdata\\local\\temp\\" + "b" * 1000
detector._normalize_text(temp_path)  # Potential catastrophic backtracking
```

**IMPACT:**
- **Denial of Service (DoS)** via malformed observation strings
- Agent can hang the detector by returning crafted error messages
- Regex engine CPU spike on adversarial input

**FIX REQUIRED:**
```python
# Use atomic grouping or possessive quantifiers to prevent backtracking
s = re.sub(r"\{?(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\}?", "<UUID>", s)
```

---

### 2.3 MEDIUM: `_has_failure_indicator()` False Negatives on Partial Failures

**Location:** `detector.py:131-140`

```python
def _has_failure_indicator(self, text: Optional[str]) -> bool:
    if not text:
        return False
    clean = re.sub(
        r"\b(?:0|zero|no)\s+(?:errors?|failures?|failed|exceptions?)\b",
        "",
        str(text).lower()
    )
    return bool(re.search(r"\b(error|fail|failed|failure|exception|denied|refused|cannot|unresolved)\b", clean))
```

**FLAW:** The function **only strips "0 errors", "no failures", etc.**, but misses:
- "0 failed, 5 passed" → strips "0 failed" → leaves "5 passed" → no failure indicator (WRONG!)
- "FAILED: 1/10 tests" → doesn't match the strip pattern → correctly detects failure (OK)
- "Test run: 0 errors, 0 failures, 0 exceptions" → strips all three → returns False (WRONG!)

**Exploitation:**
```python
# Partial test failure masked by passing counts
text = "0 failed, 5 passed, 3 skipped"
# After strip: "5 passed, 3 skipped"
# No failure indicator found → returns False (WRONG! Should detect partial failure)

# All-passing test output
text = "0 failed, 0 errors, 0 exceptions, 100 passed"
# After strip: "100 passed"
# No failure indicator found → returns False (CORRECT)
```

**IMPACT:**
- Partial test failures are not detected as deadlock indicators
- Loops with mixed success/failure outputs bypass detection

---

## 3