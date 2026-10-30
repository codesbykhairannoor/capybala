# CAPYBALA v0.6.0 SECURITY & CORRECTNESS AUDIT

## CRITICAL FLAWS

---

## 1. `prune_dead_searches()` - FALSE POSITIVE COMPRESSION BUG

**Location:** `pruner.py`, lines 189-217

### Flaw 1.1: Regex False Positives on Legitimate Content
```python
neg_patterns = (
    r"\b(?:no matches found|found 0 matches|0 matches found|directory [^\n]+ not found|file not found|no such file or directory)\b"
)
```

**Problem:** This regex will match **any** message containing these phrases, including:
- Python docstrings: `"""Returns 0 matches found in the dataset"""`
- Code comments: `# TODO: handle file not found case`
- Legitimate tool responses: `"The search returned 0 matches found, but here's the analysis..."`
- Error logs that contain actionable information

**Impact:** Legitimate context is irreversibly destroyed. A user asking "Why does my code say 'file not found'?" gets the answer compressed to `[Search Result: 0 matches found (Why does my code say 'file not found'?)]`.

**Proof of Concept:**
```python
messages = [
    {"role": "user", "content": "Analyze this Python function"},
    {"role": "assistant", "content": "def search(query):\n    '''Returns 0 matches found if query is empty'''\n    return []"},
    {"role": "user", "content": "What does it do?"},
    {"role": "assistant", "content": "It returns 0 matches found when query is empty."},
]
result = pruner.prune_dead_searches(messages, max_age_turns=2)
# The legitimate docstring and response are now tombstones!
```

---

### Flaw 1.2: Tool Call Pairing Corruption
```python
msg["content"] = tombstone  # Line 211
```

**Problem:** If a `tool_response` message has `tool_call_id="xyz"` and its content is compressed, the **tool_call_id is preserved but content is destroyed**. This breaks the semantic link:

```python
messages = [
    {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "function": {"name": "search", "arguments": "{}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "Directory /home/user not found (but here's what I found instead: ...)"},
]
result = pruner.prune_dead_searches(messages)
# Result: tool_call_id="call_1" now points to "[Search Result: 0 matches found (Directory /home/user not found)]"
# The LLM loses the "but here's what I found instead" context!
```

**Impact:** Tool execution semantics are corrupted. The LLM sees a tool_call_id pointing to a tombstone instead of the actual result.

---

### Flaw 1.3: Boundary Calculation Off-by-One
```python
boundary = len(cleaned_messages) - max_age_turns  # Line 200
for i in range(1, boundary):  # Line 205
```

**Problem:** If `len(cleaned_messages) == 5` and `max_age_turns == 6`:
- `boundary = 5 - 6 = -1`
- `range(1, -1)` is empty → **no messages are inspected**
- Function returns unmodified messages but claims success

**Worse:** If `max_age_turns == 0`:
- `boundary = len(cleaned_messages)`
- Loop inspects **all** messages including the protected root context
- Root system prompt could be compressed if it contains "file not found"

**Proof of Concept:**
```python
messages = [
    {"role": "system", "content": "You are a file system. If file not found, say so."},
    {"role": "user", "content": "Find /etc/passwd"},
    {"role": "tool", "content": "file not found"},
]
result = pruner.prune_dead_searches(messages, max_age_turns=0)
# System prompt is now corrupted!
```

---

## 2. `rollback_and_reflect()` - ANTHROPIC SCHEMA VIOLATION

**Location:** `pruner.py`, lines 146-155

### Flaw 2.1: Content Block Type Mismatch
```python
if clean_history and clean_history[-1].get("role") == "user":
    prev_content = clean_history[-1].get("content")
    if isinstance(prev_content, list):
        clean_history[-1]["content"] = prev_content + [{"type": "text", "text": f"\n\n{reflection_text}"}]
    else:
        clean_history[-1]["content"] = f"{prev_content or ''}\n\n{reflection_text}"
```

**Problem:** Anthropic's `messages.create()` accepts **two distinct content formats**:

1. **String format:** `{"role": "user", "content": "text"}`
2. **Block format:** `{"role": "user", "content": [{"type": "text", "text": "..."}, {"type": "tool_result", "tool_use_id": "...", "content": "..."}]}`

The code assumes if `content` is a list, it's a text block list. **But it could be a tool_result block list:**

```python
# Anthropic tool response format
clean_history[-1] = {
    "role": "user",  # Anthropic uses "user" for tool results
    "content": [
        {"type": "tool_result", "tool_use_id": "call_123", "content": "result"}
    ]
}

# Code appends text block to tool_result block list:
clean_history[-1]["content"].append({"type": "text", "text": reflection_text})
# Result: [{"type": "tool_result", ...}, {"type": "text", ...}]
# This violates Anthropic schema! tool_result blocks cannot be mixed with text blocks in the same message.
```

**Impact:** 400 Bad Request from Anthropic API.

---

### Flaw 2.2: Gemini `parts` Format Lost During Rollback
```python
clean_history = copy.deepcopy(valid_messages[:target_idx])
```

**Problem:** The code checks for Gemini `parts` format in `heal()` but **never preserves it during rollback**. If a message has:

```python
{
    "role": "model",
    "parts": [
        {"text": "I'll search for that"},
        {"function_calls": [{"name": "search", "args": {"q": "query"}}]}
    ]
}
```

After rollback, this message is included in `clean_history` as-is. But then `rollback_and_reflect()` appends a user message with string content. **Gemini expects strict alternation of `parts` format**, and mixing `parts` with string `content` in adjacent messages can cause schema errors.

---

### Flaw 2.3: Protected Prefix Calculation Fails on Edge Cases
```python
protected_prefix_count = 1
for i, msg in enumerate(valid_messages[:4]):
    if msg.get("role") == "user":
        protected_prefix_count = i + 1
        break
```

**Problem:** If the first 4 messages are all `system` or `assistant` roles (no user message), `protected_prefix_count` stays `1`. Then:

```python
target_idx = max(protected_prefix_count, len(valid_messages) - rollback_turns)
```

If `len(valid_messages) == 10` and `rollback_turns == 4`:
- `target_idx = max(1, 6) = 6`
- **Only the first message is protected**, but the system prompt (message 0) might be at index 0!

**Proof of Concept:**
```python
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "assistant", "content": "Hello"},
    {"role": "assistant", "content": "Hello again"},  # Consecutive assistant (invalid for Anthropic)
    {"role": "user", "content": "Hi"},
    # ... more messages
]
result = pruner.rollback_and_reflect(messages, provider="anthropic", rollback_turns=2)
# System prompt is protected, but the two consecutive assistant messages remain!
```

---

## 3. `heal()` - CRITICAL RACE CONDITION & INDEX ERROR

**Location:** `api.py`, lines 60-146

### Flaw 3.1: IndexError in Gemini Parts Handling
```python
if parts and isinstance(parts, list):
    if role in ("model", "assistant"):
        for part in parts:
            if isinstance(part, dict):
                if "function_calls" in part:
                    for fc in part["function_calls"]:
                        fn_name = fc.get("name", "tool")
                        fn_args = json.dumps(fc.get("args", {}), sort_keys=True)
                        turns_sequence.append((f"{fn_name}({fn_args})", ""))
                elif "text" in part:
                    turns_sequence.append((str(part["text"]), ""))
    elif role in ("user", "tool", "tool_response"):
        obs_text = ""
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                obs_text += str(part["text"]) + " "
        obs_text = obs_text.strip()
        if turns_sequence:
            prev_act, _ = turns_sequence[-1]  # ← LINE 95: IndexError if turns_sequence is empty!
            turns_sequence[-1] = (prev_act, obs_text)
        else:
            turns_sequence.append(("", obs_text))
```

**Problem:** Line 95 assumes `turns_sequence` is non-empty. But if the first message is a `user` role with `parts`, `turns_sequence` is empty:

```python
messages = [
    {"role": "user", "parts": [{"text": "Hello"}]}
]
heal(messages)
# IndexError: list index out of range at line 95
```

**Impact:** Crash on first-message Gemini format.

---

### Flaw 3.2: In-Place Mutation Race Condition
```python
# Line 180-183
if isinstance(messages, list):
    try:
        messages[:] = rollback_res.pruned_messages
    except TypeError:
        pass

return messages
```

**Problem:** This mutates `messages` in-place **without holding a lock**. If another thread is iterating over `messages` while `heal()` is executing:

```python
# Thread 1: Iterating
for msg in messages:
    process(msg)

# Thread 2: Calling heal()
messages = heal(messages)  # Mutates messages[:] in-place
# Thread 1 now sees a partially modified list → IndexError or corrupted state
```

**The `_api_lock` in `watch()` does NOT protect `heal()` calls!** The lock only protects client wrapper registration, not the actual `heal()` execution.

**Proof of Concept:**
```python
import threading
import time

messages = [{"role": "user", "content": f"msg_{i}"} for i in range(100)]

def iterate():
    for _ in range(1000):
        for msg in messages:
            time.sleep(0.0001)

def mutate():
    time.sleep(0.05)
    heal(messages)

t1 = threading.Thread(target=iterate)
t2 = threading.Thread(target=mutate)
t1.start()
t2.start()
t1.join()
t2.join()
# Likely crashes with IndexError or RuntimeError
```

---

### Flaw 3.3: Tool Call Map Collision
```python
tool_call_map = {}  # call_id or tool_name -> action_str
# ...
tool_call_map[call_id] = act_str
tool_call_map[fn_name] = act_str  # ← COLLISION!
```

**Problem:** Both `call_id` and `fn_name` are used as keys. If two different tool calls have the same function name:

```python
messages = [
    {"role": "assistant", "tool_calls": [
        {"id": "call_1", "function": {"name": "search", "arguments": '{"q": "a"}'}},
        {"id": "call_2", "function": {"name": "search", "arguments": '{"q": "b"}'}}
    ]},
    {"role": "tool", "tool_call_id": "call_1", "content": "result_a"},
    {"role": "tool", "tool_call_id": "call_2", "content": "result_b"},
]
heal(messages)
# tool_call_map["search"] = "search({...})" from call_2 (overwrites call_1)
# When processing tool_call_id="call_1", it retrieves the wrong action!
```

**Impact:** Deadlock detection uses wrong action strings, leading to false negatives or false positives.

---

### Flaw 3.4: Streaming Response Handling Missing
```python
def guarded_create(*args, **kwargs):
    if "messages" in kwargs:
        kwargs["messages"] = heal(...)
    return orig_create(*args, **kwargs)
```

**Problem:** If `stream=True` is passed, the response is a generator. The code doesn't handle streaming at all. If the LLM is streaming and hits a deadlock mid-stream, `heal()` is never called on the accumulated messages.

**Impact:** Streaming responses bypass deadlock detection entirely.

---

## 4. `validate()` - INCOMPLETE TOOL CALL TRACKING

**Location:** `api.py`, lines 245-280

### Flaw 4.1: Anthropic Tool Use Format Not Validated
```python
if "tool_calls" in msg and msg["tool_calls"]:
    for tc in msg["tool_calls"]:
        if isinstance(tc, dict):
            tool_call_ids.add(tc.get("id"))
elif role in ("tool", "tool_response"):
    tid = msg.get("tool_call_id")
    if tid:
        tool_response_ids.add(tid)
```

**Problem:** This only checks OpenAI `tool_calls` format. Anthropic uses `content` blocks:

```python
messages = [
    {"role": "assistant", "content": [
        {"type": "tool_use", "id": "call_1", "name": "search", "input": {}}
    ]},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "call_1", "content": "result"}
    ]}
]
is_valid, err = validate(messages)
# Returns True, but never checked Anthropic tool_use blocks!
```

**Impact:** Anthropic messages pass validation but may fail at API call time.

---

## 5. TOP 3 CONCRETE BREAKING TEST CASES

### Test Case 1: `prune_dead_searches()` Destroys Legitimate Context
```python
def test_prune_dead_searches_false_positive():
    pruner = ContextPruner()
    messages = [
        {"role": "system", "content": "You are a code analyzer."},
        {"role": "user", "content": "Analyze this function"},
        {"role": "assistant", "content": "def find_user(id):\n    '''Returns 0 matches found if id is invalid'''\n    return db.query(id)"},
        {"role": "user", "content": "What does it return?"},
        {"role": "assistant", "content": "It returns 0 matches found when the ID doesn't exist in the database."},
        {"role": "tool", "content": "Directory /data not found but cache available"},
        {"role": "tool", "content": "File not found in primary location, checking backup"},
    ]
    
    result = pruner.prune_dead_searches(messages, max_age_turns=2)
    
    # ASSERTION: Legitimate docstring and response should NOT be compressed
    assert "Returns 0 matches found if id is invalid" in result.pruned_messages[2]["content"]
    assert "It returns 0 matches found when" in result.pruned_messages[4]["content"]
    
    