# 🦫 Capybala v0.8.0: Multi-Model Adversarial Audit Report

**Audit Panel**: Claude-Haiku-4.5 (Anthropic), DeepSeek-V3, Qwen-2.5-Coder-32B
**Total Cost**: $0.01719 USD (Strict budget safeguard preserved)
**Timestamp**: 2026-10-31 10:11:22 UTC

---

## 🤖 Auditor: Claude-Haiku-4.5 (`anthropic/claude-haiku-4.5`)

- **Execution Time**: 5.96s
- **Tokens**: 34627 | **Cost**: ~$0.01116 USD

# CAPYBALA v0.8.0 HARDCORE TECHNICAL AUDIT

## EXECUTIVE SUMMARY
**VERDICT: NOT PRODUCTION-READY. Multiple critical bugs, architectural inconsistencies, and false-positive traps lurk beneath marketing claims. Estimated 6-8 week remediation required.**

---

## 1. CLAIM VS REALITY CHECK

### 1.1 **O(1) Space Claim** ❌ PARTIALLY FALSE
**Claim:** "Zero memory pinning: ring buffer stores 16-byte SHA digests and compact previews."

**Reality:**
- ✅ `action_history`, `obs_hash_history` use bounded `deque(maxlen=24)` → O(1) space per buffer
- ❌ **HIDDEN LEAK:** `raw_actions` stores **512-character strings** (line 195):
  ```python
  self.raw_actions: deque = deque(maxlen=history_window)
  ...
  self.raw_actions.append(raw_action[:512])  # 512 chars × 24 = 12KB per detector instance
  ```
  Under multi-agent scenarios with 100+ detectors, this becomes **1.2MB+ heap retention**.

- ❌ **ATTRACTOR VECTOR LEAK:** `vector_history` stores **1024-float vectors** (attractor.py:52):
  ```python
  self.vector_history: deque = deque(maxlen=window_size)  # window_size=12
  # 12 × 1024 floats × 8 bytes = 98KB per attractor detector
  ```
  With 10 concurrent agents: **~1MB heap churn per cycle**.

- ❌ **SEMANTIC FEATURE HASHING:** `_extract_feature_vector()` creates temporary `defaultdict(float)` with unbounded feature keys (attractor.py:77-85). Under adversarial input (e.g., 100K unique tokens), this explodes to **multi-MB allocations**.

**Verdict:** O(1) claim is **OVERSTATED**. Real space complexity is O(window_size × vector_dim) = O(12 × 1024) = O(12,288) per attractor, plus O(512 × 24) = O(12,288) per detector. Acceptable but not "zero-overhead."

---

### 1.2 **Attractor Manifold Mathematical Validity** ❌ FUNDAMENTALLY FLAWED

**Claim:** "Post-IF-ELSE Semantic Attractor & Manifold Engine" detects "ergodic traps" via Markov entropy and semantic velocity.

**Reality:**

#### **Problem 1: Velocity Metric is Meaningless**
```python
def _compute_semantic_velocity(self, v_curr, v_prev):
    cos_sim = self._cosine_similarity(v_curr, v_prev)
    return max(0.0, 1.0 - cos_sim)  # velocity = 1 - cos_sim
```
- **Issue:** Cosine similarity between **unit vectors** is already normalized to [-1, 1]. Subtracting from 1 gives [0, 2], but clamped to [0, 1].
- **Flaw:** This is NOT a velocity in any dynamical systems sense. It's just "1 minus cosine distance."
- **False Positive:** Two completely unrelated actions (e.g., `grep foo` vs `cat bar`) will have cos_sim ≈ 0.3, yielding velocity ≈ 0.7, which **exceeds the threshold of 0.70**, falsely declaring "exploration" when the agent is actually stuck.

#### **Problem 2: Markov Entropy Calculation is Broken**
```python
def _compute_markov_entropy(self, vectors):
    states = [self._discretize_action(v) for v in vectors]
    transitions = defaultdict(int)
    for i in range(len(states) - 1):
        s_from = states[i]
        s_to = states[i + 1]
        transitions[(s_from, s_to)] += 1
        outgoing[s_from] += 1
    entropy = 0.0
    for (s_from, s_to), count in transitions.items():
        total = outgoing[s_from]
        p_ij = count / total
        entropy -= p_ij * math.log(p_ij)
```
- **Issue:** With only 3-4 vectors (typical stagnation_steps=3), you have **at most 2-3 transitions**. Entropy of 2-3 transitions is **always low** (< 1.5 bits), regardless of whether the agent is truly stuck.
- **False Positive:** Any 3-turn sequence will likely trigger the attractor detector because entropy will be < 1.5 by definition.
- **Proof:** With 64 possible states and 3 transitions, max entropy ≈ log(3) ≈ 1.1 bits. Threshold is 1.50. **Detector will fire on almost any 3-turn sequence.**

#### **Problem 3: Discretization Loses Information**
```python
def _discretize_action(self, vector):
    indexed = heapq.nlargest(4, enumerate(vector), key=lambda x: x[1])
    state = sum((idx * (pos + 1)) for pos, (idx, val) in enumerate(indexed) if val > 0)
    return state % 64
```
- **Issue:** Hashing the top-4 indices into 64 states creates **massive collisions**. Two semantically different actions can easily map to the same state.
- **False Negative:** Genuine oscillations (A → B → A → B) might map to the same state repeatedly, making entropy calculation meaningless.

**Verdict:** Attractor manifold is **PSEUDOSCIENCE**. The mathematical foundation is unsound. It will produce **both false positives and false negatives** unpredictably.

---

### 1.3 **Invariant Guarantees in Pruner** ❌ BROKEN

**Claim:** "Zero orphan tool calls or responses across OpenAI, Anthropic, and Llama Stack."

**Reality:**

#### **Bug 1: Orphan Detection Doesn't Account for Streaming**
```python
def rollback_and_reflect(self, messages, ...):
    # Protects root context
    protected_prefix_count = 1
    for i, msg in enumerate(valid_messages[:4]):
        if msg.get("role") == "user":
            protected_prefix_count = i + 1
            break
```
- **Issue:** If the first 4 messages are all `role: "assistant"` (e.g., streaming chunks), the loop never breaks, and `protected_prefix_count` stays 1.
- **Result:** The pruner can delete the actual first user prompt, leaving only system instructions.
- **Consequence:** LLM loses task context entirely.

#### **Bug 2: Tool Response Synthesis is Anthropic-Incompatible**
```python
# validator.py line 220
synth_response = {
    "role": "tool",
    "tool_call_id": call_id,
    "name": tc.get("function", {}).get("name", "tool"),
    "content": "[Capybala Auto-Healed: ...]"
}
```
- **Issue:** Anthropic Claude **does NOT support** `role: "tool"`. It requires `role: "user"` with `content: [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]`.
- **Result:** Synthesized responses will cause **400 Bad Request** on Anthropic, defeating the entire "zero orphan" guarantee.

#### **Bug 3: Turn Alternation Repair is Incomplete**
```python
# pruner.py: No explicit turn alternation repair for Anthropic
# Only checks in validate() but doesn't fix
```
- **Issue:** If messages have consecutive `role: "user"` blocks, the pruner doesn't repair them. It only detects in `validate()`.
- **Result:** Anthropic will reject with 400 Bad Request.

**Verdict:** Invariant guarantees are **ILLUSORY**. Multiple provider-specific bugs will cause API rejections.

---

## 2. INTER-MODULE INCONSISTENCY & SCHEMA HAZARDS

### 2.1 **Detector ↔ Attractor Desync**

**Issue:** Detector calls `attractor_detector.inspect_step()` but doesn't validate return types:
```python
# detector.py line 1010
is_attractor, confidence, attractor_details = self.attractor_detector.inspect_step(
    raw_action,
    is_failing=current_fail
)
if is_attractor:
    detected_event = DeadlockEvent(...)
```

**Problem:** If `inspect_step()` returns `(True, 0.5, "")` (empty details), the `DeadlockEvent` will have:
```python
details=attractor_details  # Empty string!
```
This breaks logging and debugging. The flight recorder will print:
```
🦫  Capybala Cycle Intercepted []
```

### 2.2 **Healer ↔ Pruner Desync**

**Issue:** Healer injects `role: "user"` messages, but pruner's `rollback_and_reflect()` doesn't account for this:
```python
# healer.py line 130
injected_msg = {
    "role": "user",
    "content": doctor_directive
}

# pruner.py line 85: Protects only first user message
for i, msg in enumerate(valid_messages[:4]):
    if msg.get("role") == "user":
        protected_prefix_count = i + 1
        break
```

**Problem:** If the healer injects a `role: "user"` message, and then the pruner is called again, the pruner might treat this injected message as a "real" user turn and protect it, causing **double-injection** of recovery guidance.

**Consequence:** LLM sees:
```
[CAPYBALA DOCTOR INTERVENTION] ... [CAPYBALA

---

## 🤖 Auditor: DeepSeek-V3 (`deepseek/deepseek-chat`)

- **Execution Time**: 2.72s
- **Tokens**: 28061 | **Cost**: ~$0.00405 USD

### **Capybala v0.8.0 Technical Audit**  

#### **1. Claim vs Reality Check**  
- **O(1) Space Complexity**: **VALID**. Ring buffers (`deque(maxlen=N)`) enforce strict bounds. Murmur-like hashing (SHA-256 truncation) ensures fixed-size digests.  
- **Attractor Manifold**: **PARTIALLY VALID**. The 1024-D unit vector projection is sound, but cosine similarity thresholds (`VELOCITY_THRESHOLD=0.7`) are empirically tuned—no theoretical guarantee of avoiding false positives in high-entropy command paraphrasing.  
- **Invariant Guarantees**: **WEAK**. Schema validator repairs JSON orphans, but `pruner.py` lacks idempotency checks for repeated rollbacks (risk of context corruption after multiple interventions).  

#### **2. Inter-Module Inconsistencies**  
- **DeadlockEvent → Pruner Mismatch**: `detector.py` emits `DeadlockEvent` with `pattern_type`, but `pruner.py` ignores it, using a generic `deadlock_reason` (line 235). This loses diagnostic granularity.  
- **Healer Over-Optimism**: `healer.py` assumes `error_signature` is parseable (line 112), but `detector.py` may return `None` for non-error stagnation (e.g., `output_stagnation` without exceptions).  
- **Schema Hazard**: `validator.py` repairs JSON post-hoc, but `detector.py`’s `_sanitize_action` (line 148) may already have mutated malformed tool args, causing hash divergence.  

#### **3. Top 3 Concrete Bugs**  
1. **False Positive on Active Code Refinement**:  
   - **Location**: `detector.py`, `_is_active_code_refinement()` (line 513)  
   - **Bug**: If syntax errors persist *across* edits (e.g., indentation), the SHA-256 comparison fails to detect stagnation, leaking false negatives.  

2. **Thread-Unsafe Circuit Breaker**:  
   - **Location**: `api.py`, `heal()` (line 320)  
   - **Bug**: `prior_interventions` counter races under concurrent calls. The `_api_lock` protects pruning but not this counter.  

3. **Anthropic Turn Alternation Breakage**:  
   - **Location**: `pruner.py`, `rollback_and_reflect()` (line 188)  
   - **Bug**: Merging recovery text into existing `user` role (line 218) can violate Claude’s strict alternation if the prior message was also `user`.  

#### **4. Multi-Threading Assessment**  
- **Strengths**:  
  - `detector.py` uses `threading.RLock` per-instance (line 97).  
  - `pruner.py` and `api.py` have global `RLock` (line 30, 320).  
- **Weaknesses**:  
  - **Shared Mutable State**: `healer.py`’s `supervisor_client` is unprotected (line 24).  
  - **AsyncIO Risk**: `api.py`’s `watch()` wraps clients but doesn’t guard against async context switches during `heal()`.  

#### **5. Final Verdict**  
**GG (Production-Ready) with Caveats**:  
- **Strengths**: Bounded memory, rigorous schema repair, and semantic attractor math are legit.  
- **Deal-Breakers**: None, but **must fix**:  
  1. Thread-unsafe counters in `api.py`.  
  2. Anthropic turn alternation in `pruner.py`.  
  3. Edge-case SHA-256 stagnation detection in `detector.py`.  
- **Recommendation**: Add idempotency checks to `pruner.py` and document strict thread-local usage for `healer.py`.  

**Score**: 8.5/10 — **GG if patched**.

---

## 🤖 Auditor: Qwen-2.5-Coder-32B (`qwen/qwen-2.5-coder-32b-instruct`)

- **Execution Time**: 2.01s
- **Tokens**: 26701 | **Cost**: ~$0.00199 USD

### Technical Evaluation of Capybala v0.8.0

#### 1. Claim vs Reality Check

**Attractor Manifold Detection:**
- **Claim:** Uses hybrid word token + subword n-gram feature hashing into a 1024-D unit vector space, semantic velocity tracking, and Markov transition entropy gating.
- **Reality:** 
  - **Feature Hashing:** The `_extract_feature_vector` method uses MD5 hashing to project features into a 1024-D space. This is not a Murmur hash, but it serves a similar purpose of reducing dimensionality.
  - **Semantic Velocity:** The `_compute_semantic_velocity` method calculates the cosine similarity between vectors, which is valid for detecting semantic similarity.
  - **Markov Transition Entropy:** The `_compute_markov_entropy` method computes the Shannon entropy of state transitions, which is a valid approach for detecting ergodic traps.
  - **Mathematical Validity:** The mathematical constructs are sound, but the choice of MD5 for hashing could be improved for cryptographic security and collision resistance. However, for this application, MD5 is likely sufficient.

**O(1) Tracking:**
- **Claim:** Uses bounded memory buffers to store compact digests (16-byte SHA digests and compact previews).
- **Reality:** 
  - The use of `deque` with `maxlen` ensures that the memory usage is bounded, but the complexity of operations like `_calculate_fuzzy_similarity` and `_compute_markov_entropy` are not O(1). They depend on the size of the input data and the number of elements in the history.
  - **Conclusion:** While the memory usage is bounded, the operations themselves are not O(1).

**Invariant Guarantees:**
- **Claim:** Ensures zero orphan tool calls or responses, strict turn alternation for Anthropic Claude, and no caller message pollution.
- **Reality:** 
  - The `SchemaValidator` class in `validator.py` ensures that tool calls and responses are properly paired and that roles alternate correctly for Anthropic Claude.
  - **Conclusion:** The invariant guarantees are implemented correctly.

#### 2. Inter-Module Inconsistency & Schema Hazards

**Detector Events, Pruner Actions, and Healer Doctor Injections:**
- **Detector Events:** The `DeadlockDetector` class in `detector.py` identifies various types of deadlocks and generates `DeadlockEvent` objects.
- **Pruner Actions:** The `ContextPruner` class in `pruner.py` performs atomic checkpoint rollbacks and injects recovery guidance based on the `DeadlockEvent`.
- **Healer Doctor Injections:** The `AgentHealer` class in `healer.py` generates constructive forward directives based on the `DeadlockEvent`.

**Inconsistencies:**
- **Schema Validation:** The `validate` and `repair` functions in `validator.py` ensure that the message schema is correct before processing. However, there is no explicit check in `detector.py` or `healer.py` to ensure that the messages are schema-compliant before processing.
- **Concurrency Handling:** Both `detector.py` and `pruner.py` use `threading.RLock` for thread safety, but there is no explicit synchronization between these modules. This could lead to race conditions if multiple threads are processing the same message history simultaneously.

#### 3. Top 3 Concrete Hidden Bugs / Edge-Case Failures

1. **False Positive Detection in `_calculate_fuzzy_similarity`:**
   - **Line:** `detector.py`, `_calculate_fuzzy_similarity`
   - **Issue:** The method calculates fuzzy similarity using token overlap and 3-gram character shingles. However, it does not handle cases where the input strings are very short or contain only stop words, leading to incorrect similarity scores.
   - **Fix:** Add checks for minimum string length and filter out stop words before calculating similarity.

2. **Incorrect Role Handling in `_is_navigation_command`:**
   - **Line:** `detector.py`, `_is_navigation_command`
   - **Issue:** The method checks for navigation commands by looking for specific prefixes. However, it does not handle cases where the command is wrapped in a tool call or has additional arguments.
   - **Fix:** Extend the regex to handle more complex command structures and additional arguments.

3. **Potential Infinite Loop in `_compute_markov_entropy`:**
   - **Line:** `attractor.py`, `_compute_markov_entropy`
   - **Issue:** The method calculates the Shannon entropy of state transitions. If the state transitions are highly unpredictable, the entropy could be very high, leading to incorrect detection of attractors.
   - **Fix:** Introduce a threshold for entropy to ensure that only truly low-entropy states are considered attractors.

#### 4. Multi-threading & Concurrency Assessment

- **Thread Safety:** Both `detector.py` and `pruner.py` use `threading.RLock` for thread safety, which is appropriate for protecting shared resources.
- **Concurrency Handling:** The `api.py` module wraps client methods to ensure that the `heal` function is called in a thread-safe manner. However, there is no explicit synchronization between the detector, pruner, and healer modules, which could lead to race conditions.
- **AsyncIO Support:** The `watch` function in `api.py` supports both synchronous and asynchronous client methods, ensuring that the system can handle both types of operations.

#### 5. Final Objective Verdict

**Verdict:**
- **Pros:**
  - Robust deadlock detection mechanisms.
  - Effective schema validation and repair.
  - Thread-safe operations.
- **Cons:**
  - Potential false positives in fuzzy similarity calculations.
  - Incorrect role handling in navigation command detection.
  - Lack of explicit synchronization between detector, pruner, and healer modules.
  - Operations are not strictly O(1) due to the complexity of similarity and entropy calculations.

**Conclusion:**
Capybala v0.8.0 is a well-designed system with robust deadlock detection and schema validation mechanisms. However, there are several areas for improvement, particularly in handling edge cases and ensuring complete synchronization between modules. With these improvements, Capybala could be considered production-ready ('GG'). Currently, it has some lurking deal-breakers that need to be addressed.

---

