# Capybala v0.8.0 Raw Unbiased AI Audit (Zero Prompt Injection)

**Audit Timestamp:** 2026-10-31 15:32:18  
**Reviewing Models:** DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5  

---

## ⚖️ Audit by DeepSeek-V3

### 1. CODE QUALITY & ALGORITHMIC CORRECTNESS

**Does the code do what it claims?**  
Yes, the code implements a semantic loop detector with the claimed features:
- Hybrid word token + subword n-gram feature hashing (though the docstring says 256-D but the code uses 1024-D)
- Semantic velocity tracking via cosine similarity
- Markov transition entropy gating
- Exemption logic for navigation/editing commands

**Feature Hashing (1024-D):**  
- Correctly uses MD5 hashing modulo `HASH_SPACE` (1024) to project features into a fixed-dimensional space.
- L2 normalization is correctly implemented and numerically stable (checks `norm > EPSILON`).
- **Issue:** The docstring claims 256-D but the code uses 1024-D. This inconsistency should be fixed.

**Semantic Velocity:**  
- Correctly computes `1 - cosine_similarity` between consecutive vectors.
- Handles edge cases (empty vectors) and clamps values to `[-1, 1]`.
- Numerically stable.

**Shannon Entropy:**  
- Correctly computes Markov transition entropy using discretized states.
- Handles division by zero and log(0) via `EPSILON` checks.
- **Minor Issue:** The default return value of `2.0` when `len(vectors) < 3` is arbitrary. A better approach might be to return `math.log(64)` (max entropy for 64 states).

### 2. BUGS, VULNERABILITIES, AND EDGE CASES

**Bugs and Logic Errors:**  
1. **Inconsistent Hashing Dimensions:**  
   - Docstring claims 256-D, but code uses 1024-D. This could mislead users.

2. **Discretization Bias in `_discretize_action`:**  
   - The method `_discretize_action` uses `heapq.nlargest(4, ...)` to select top features, but the weighting `(idx * (pos + 1))` is arbitrary and may not preserve semantic meaning well. This could lead to unstable state transitions.

3. **Velocity Threshold Logic:**  
   - The condition `if mean_vel > self.velocity_threshold` returns early, but `mean_vel` is compared against a threshold meant for individual velocities. This might miss some edge cases where mean velocity is slightly below threshold but individual steps oscillate.

4. **Exemption Logic Overlap:**  
   - The `_is_exempt_action` method checks both tool calls and first tokens, but there’s redundancy (e.g., `edit` is checked in both places). This could be streamlined.

5. **Failure History Handling:**  
   - The check `if sum(recent_failures) < min_required_failures` uses integer division (`// 2`), which might not be optimal for even-sized windows. A better approach might be `ceil(stagnation_steps / 2)`.

**Performance Bottlenecks:**  
1. **MD5 Hashing:**  
   - While MD5 is fast, it’s not cryptographically secure (not a concern here) and may collide more than modern alternatives (e.g., `xxhash`). For a 1024-D space, this is likely fine, but worth noting.

2. **Cosine Similarity:**  
   - The current implementation is O(n) for vector dimension, which is fine for 1024-D but could be optimized with NumPy if performance becomes critical.

3. **Markov Entropy Calculation:**  
   - The nested loops over transitions are O(n²) in the worst case (for 64 states, this is 4096 iterations). This is acceptable for `window_size=12`, but could become slow for larger windows.

**Edge Cases:**  
1. **Empty or Garbage Inputs:**  
   - The code handles empty strings gracefully but doesn’t sanitize inputs (e.g., very long strings could cause memory issues in `_extract_feature_vector`).

2. **All-Zero Vectors:**  
   - If all features hash to the same bucket (unlikely but possible), the L2 norm could be zero. The code correctly handles this with `EPSILON`.

3. **Single-State Markov Chain:**  
   - If all actions discretize to the same state, entropy will be 0. This is correct but could be called out explicitly in the docstring.

### 3. PRODUCTION READINESS & SCORES

**Algorithmic Correctness: 8/10**  
- The core logic is sound, but the discretization method and velocity thresholding could be more robust.
- The docstring inaccuracy (256-D vs. 1024-D) is a minor but notable issue.

**Production Readiness: 7/10**  
- **Pros:**  
  - No external dependencies (pure Python).  
  - Good numerical stability (EPSILON checks, clamping).  
  - Clear, modular methods.  
- **Cons:**  
  - Arbitrary constants (e.g., `2.5` weight for word tokens, `64` states) could benefit from tuning or configuration.  
  - The discretization method (`_discretize_action`) is heuristic and may not generalize well.  
  - Could benefit from more unit tests (e.g., for edge cases like all-identical actions).  

**Concrete Recommendations:**  
1. Fix the docstring to reflect 1024-D hashing.  
2. Replace `heapq.nlargest(4, ...)` with a more principled discretization method (e.g., k-means clustering if performance allows).  
3. Use `math.ceil` for `min_required_failures` to handle even-sized windows better.  
4. Add a benchmark/test for very long input strings to ensure no memory issues.  
5. Consider adding a `validate_config()` method to check that thresholds are sane (e.g., `velocity_threshold < 1.0`).  

Overall, this is a well-engineered and mostly correct implementation, but could benefit from minor refinements for production use.

---

## ⚖️ Audit by GPT-4o-mini

### 1. CODE QUALITY & ALGORITHMIC CORRECTNESS

**Does this code do what it claims?**
- The code appears to implement a semantic loop detection mechanism as described in the comments. It uses feature extraction, semantic velocity, and Markov transition entropy to identify potential attractor loops in agent actions.

**Are the feature hashing (1024-D), semantic velocity, and Shannon entropy calculations correct and numerically stable?**
- **Feature Hashing**: The feature hashing mechanism uses MD5 to hash features into a 1024-dimensional space. While this approach is generally effective for reducing dimensionality, MD5 is not collision-resistant for cryptographic purposes. However, for this application, it is acceptable as long as the hash space is sufficiently large to minimize collisions.
- **Semantic Velocity**: The calculation of semantic velocity as `1 - cosine_similarity` is mathematically sound. However, the thresholds used (0.7 for high velocity and 0.55 for low velocity) are somewhat arbitrary and should be empirically validated.
- **Shannon Entropy**: The entropy calculation appears to be implemented correctly. It accounts for the probabilities of transitions between states and uses the correct formula. However, the handling of cases with fewer than three vectors (returning a default high entropy of 2.0) may not be ideal, as it could lead to false positives in certain scenarios.

### 2. BUGS, VULNERABILITIES, AND EDGE CASES

**Bugs and Logic Errors:**
- **Velocity Calculation**: The `_compute_semantic_velocity` method does not handle the case where `v_prev` is a zero vector (which could happen if the action is empty or invalid). This could lead to a division by zero or misleading velocity values.
- **Entropy Calculation**: The method `_compute_markov_entropy` does not handle the case where there are no transitions (i.e., if `outgoing[s_from]` is zero). This could lead to a division by zero error.
- **Action History Check**: In the `inspect_step` method, the check for identical recent actions (`len(set(list(self.action_history)[-self.stagnation_steps - 1:])) <= 1`) could lead to false negatives if the last action was valid but the previous actions were not.

**Performance Bottlenecks:**
- The use of `deque` for history tracking is efficient, but the repeated calls to `list()` in `inspect_step` can lead to unnecessary overhead. Instead, directly accessing the `deque` elements would be more efficient.
- The entropy calculation could be optimized by using a more efficient data structure for counting transitions, such as a `Counter` from the `collections` module.

**Edge Cases:**
- The `_extract_feature_vector` method may return a zero vector if the input string is empty or contains only whitespace. This could lead to misleading results in subsequent calculations.
- The method `_is_exempt_action` may not cover all potential exempt actions, leading to false positives or negatives in attractor detection.

### 3. PRODUCTION READINESS & SCORES

**Algorithmic Correctness: 7/10**
- The core algorithms for feature extraction, semantic velocity, and entropy calculation are sound, but there are several edge cases and potential bugs that could lead to incorrect behavior in production. The reliance on arbitrary thresholds without empirical validation is also a concern.

**Production Readiness: 6/10**
- The code is relatively clean and well-structured, but it lacks comprehensive error handling and edge case management. The performance could be improved, and the use of MD5 for hashing, while acceptable for this context, could be reconsidered for better collision resistance. Additionally, the documentation could be enhanced to clarify the rationale behind certain design choices and thresholds.

**Concrete Critique:**
- The implementation is a solid foundation for a semantic loop detection system, but it requires further testing and validation to ensure robustness in various scenarios. The handling of edge cases, particularly around empty inputs and transition counts, needs to be addressed. Additionally, empirical testing should be conducted to determine optimal thresholds for velocity and entropy to improve the accuracy of the detection mechanism.

---

## ⚖️ Audit by Claude-Haiku-4.5

# Code Audit: `capybala/attractor.py`

## 1. CODE QUALITY & ALGORITHMIC CORRECTNESS

### ✅ What It Claims vs. What It Does

The module claims to detect semantic loops via:
1. **Hybrid word token + character n-gram feature hashing** → 1024-D unit vectors
2. **Semantic velocity tracking** → 1 - cos_sim(v_t, v_t-1)
3. **Markov transition entropy gating** → Shannon entropy of discretized state transitions

**Assessment**: The implementation broadly matches the claims, but with significant caveats (see below).

---

### ⚠️ Feature Hashing: CORRECT BUT OVERSOLD

**Code:**
```python
def _extract_feature_vector(self, text: str) -> List[float]:
    # ... feature extraction ...
    vector = [0.0] * self.HASH_SPACE  # 1024 buckets
    for feat, weight in features.items():
        h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16) % self.HASH_SPACE
        vector[h] += weight
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > self.EPSILON:
        vector = [v / norm for v in vector]
    return vector
```

**Issues:**

1. **Hash collision claim is FALSE**: The docstring claims "virtually eliminates hash collisions under birthday paradox" for 1024-D space. This is **mathematically incorrect**. 
   - Birthday paradox: ~√(1024) ≈ 32 features needed for 50% collision probability
   - With typical text, you'll easily have 100+ features → **guaranteed collisions**
   - The code doesn't handle collisions; it just accumulates weights (which is fine, but the claim is misleading)

2. **MD5 is overkill**: Using MD5 for feature hashing is unnecessary overhead. A simpler hash (e.g., `hash()`) would suffice and be faster.

3. **Feature weighting is ad-hoc**: Word tokens get 2.5x weight, character 3-grams get 1.0x. No justification provided. This is a hyperparameter that should be tunable or justified empirically.

---

### ⚠️ Semantic Velocity: CORRECT BUT QUESTIONABLE SEMANTICS

**Code:**
```python
def _compute_semantic_velocity(self, v_curr: List[float], v_prev: List[float]) -> float:
    cos_sim = self._cosine_similarity(v_curr, v_prev)
    return max(0.0, 1.0 - cos_sim)
```

**Assessment**: 
- ✅ Mathematically correct: velocity = 1 - cos_sim is a valid distance metric
- ⚠️ **Semantic interpretation is weak**: Cosine similarity on hashed features doesn't guarantee semantic similarity. Two completely different commands could hash to similar buckets by chance.
- ⚠️ **Threshold of 0.70 is arbitrary**: No empirical justification. Why not 0.65 or 0.75?

---

### ❌ Markov Entropy: CORRECT MATH, FLAWED LOGIC

**Code:**
```python
def _compute_markov_entropy(self, vectors: List[List[float]]) -> float:
    if len(vectors) < 3:
        return 2.0  # Safe default (high entropy)
    
    states = [self._discretize_action(v) for v in vectors]
    transitions: Dict[Tuple[int, int], int] = defaultdict(int)
    outgoing: Dict[int, int] = defaultdict(int)
    
    for i in range(len(states) - 1):
        s_from = states[i]
        s_to = states[i + 1]
        transitions[(s_from, s_to)] += 1
        outgoing[s_from] += 1
    
    entropy = 0.0
    for (s_from, s_to), count in transitions.items():
        total = outgoing[s_from]
        if total > 0:
            p_ij = count / total
            if p_ij > self.EPSILON:
                entropy -= p_ij * math.log(p_ij)
    
    return entropy
```

**Issues:**

1. **Discretization is lossy and unstable**:
   ```python
   def _discretize_action(self, vector: List[float]) -> int:
       indexed = heapq.nlargest(4, enumerate(vector), key=lambda x: x[1])
       state = sum((idx * (pos + 1)) for pos, (idx, val) in enumerate(indexed) if val > 0)
       return state % 64
   ```
   - Takes top-4 indices, multiplies by position weight, sums, then mod 64
   - **This is arbitrary and non-deterministic** (order of `heapq.nlargest` ties is undefined)
   - Two very similar vectors could map to completely different states
   - **Result**: Entropy calculation becomes unreliable

2. **Entropy calculation is incomplete**:
   - Only computes row-wise entropy (per source state)
   - Should compute **joint entropy** or **conditional entropy** for proper Markov analysis
   - Current approach doesn't capture the full transition matrix structure

3. **Default entropy of 2.0 is arbitrary**: Why 2.0? For a 64-state system, max entropy is log(64) ≈ 4.16. This default is neither justified nor consistent.

---

### ⚠️ Cosine Similarity: CORRECT BUT INCOMPLETE

**Code:**
```python
def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(-1.0, min(1.0, dot))
```

**Issues:**
- ✅ Mathematically correct for unit vectors
- ⚠️ **Assumes vectors are already normalized**: If not, this is wrong. The code does normalize in `_extract_feature_vector`, but this assumption is implicit and fragile.
- ⚠️ **No length check**: If `v1` and `v2` have different lengths, `zip` silently truncates. Should validate.

---

## 2. BUGS, LOGIC ERRORS, AND EDGE CASES

### 🔴 BUG #1: Axiom 3 Logic Error

**Code:**
```python
# Axiom 3: If all recent actions in the window are literally identical strings, Tier 1 handles it
if len(set(list(self.action_history)[-self.stagnation_steps - 1:])) <= 1:
    return False, 0.0, ""
```

**Problem**: 
- Takes `stagnation_steps + 1` actions (e.g., 4 actions if `stagnation_steps=3`)
- Checks if they're all identical
- **Logic is backwards**: If they ARE identical, this detector should NOT fire (correct), but the comment is confusing
- **Edge case**: If `action_history` has fewer than `stagnation_steps + 1` items, this silently passes (should be explicit)

---

### 🔴 BUG #2: Failure Threshold Logic

**Code:**
```python
recent_failures = list(self.failure_history)[-self.stagnation_steps:]
min_required_failures = (self.stagnation_steps // 2) + 1
if sum(recent_failures) < min_required_failures:
    return False, 0.0, ""
```

**Problem**:
- For `stagnation_steps=3`: `min_required_failures = 3//2 + 1 = 2`
- Requires 2 out of 3 failures (67%)
- **Inconsistent with docstring**: "3 transitions (4 turns)" suggests 4 steps, but code uses 3
- **Off-by-one risk**: If `failure_history` has fewer than 3 items, `list()[-3:]` returns fewer items, and the check becomes unreliable

---

### 🔴 BUG #3: Velocity History Length Mismatch

**Code:**
```python
if len(self.vector_history) >= 2:
    velocity = self._compute_semantic_velocity(...)
    self.velocity_history.append(velocity)
else:
    return False, 0.0, ""

if len(self.velocity_history) < self.stagnation_steps:
    return False, 0.0, ""

recent_velocities = list(self.velocity_history)[-self.stagnation_steps:]
```

**Problem**:
- `velocity_history` has `maxlen=window_size` (12 by default)
- But we check `len(self.velocity_history) < self.stagnation_steps` (3 by default)
- Then we take `[-self.stagnation_steps:]` (last 3)
- **If `velocity_history` has 3-11 items, we proceed with fewer than expected**
- Should check `len(self.velocity_history) >= self.stagnation_steps` (currently does, but the logic is fragile)

---

### 🔴 BUG #4: Confidence Calculation Overflow

**Code:**
```python
vel_score = max(0.0, 1.0 - (mean_vel / self.velocity_threshold))
ent_score = max(0.0, 1.0 - (entropy / self.entropy_threshold))
confidence = round(min(1.0, (vel_score * 0.6 + ent_score * 0.4)), 3)
```

**Problem**:
- If `mean_vel = 0.1` and `velocity_threshold = 0.7`: `vel_score = 1.0 - (0.1/0.7) = 0.857`
- If `entropy = 0.5` and

---

