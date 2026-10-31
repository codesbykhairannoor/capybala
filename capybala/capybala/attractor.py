"""
capybala.attractor
~~~~~~~~~~~~~~~~~~
Post-IF-ELSE Mathematical Deadlock Detection Engine.
Detects semantic loops, paraphrased command oscillations, and ergodic traps using:
1. Hybrid Word Token + Subword N-Gram Feature Hashing (1024-D Unit Vector Space)
2. Semantic Velocity Tracking: v_t = 1 - cos_sim(v_t, v_t-1)
3. Markov Transition Entropy Gating: H = -Σ p_ij * log(p_ij)

Zero External Dependencies: Pure Python standard library (no PyTorch, no NumPy).
Latency: < 0.8 ms per action.
"""

import math
import hashlib
import heapq
import re
from collections import defaultdict, deque
from typing import List, Tuple, Dict, Optional, Set


class SemanticAttractorDetector:
    """
    Mathematical detector for continuous semantic attractor loops and ergodic traps.
    Detects when an agent is running semantically equivalent operations with different
    syntactic formulations (e.g., paraphrased bash commands or equivalent python scripts).
    """

    NGRAM_SIZE: int = 3
    HASH_SPACE: int = 1024            # 1024-D unit sphere projection (virtually eliminates hash collisions under birthday paradox)
    VELOCITY_THRESHOLD: float = 0.70  # Below 0.70 indicates strong semantic gravity / attractor
    VARIANCE_THRESHOLD: float = 0.08  # Stagnation variance bound (distinguishes true attractor from wide oscillation)
    ENTROPY_THRESHOLD: float = 1.50   # Low entropy = predictable/trapped state transitions
    WINDOW_SIZE: int = 12
    STAGNATION_STEPS: int = 3         # 3 transitions (4 turns) of persistent semantic stagnation
    EPSILON: float = 1e-9

    def __init__(
        self,
        velocity_threshold: float = VELOCITY_THRESHOLD,
        variance_threshold: float = VARIANCE_THRESHOLD,
        entropy_threshold: float = ENTROPY_THRESHOLD,
        stagnation_steps: int = STAGNATION_STEPS,
        window_size: int = WINDOW_SIZE,
    ):
        self.velocity_threshold = velocity_threshold
        self.variance_threshold = variance_threshold
        self.entropy_threshold = entropy_threshold
        self.stagnation_steps = stagnation_steps
        self.window_size = window_size

        self.action_history: deque = deque(maxlen=window_size)
        self.vector_history: deque = deque(maxlen=window_size)
        self.velocity_history: deque = deque(maxlen=window_size)
        self.failure_history: deque = deque(maxlen=window_size)
        self.total_attractors_detected = 0

    def _extract_feature_vector(self, text: str) -> List[float]:
        """
        Extracts hybrid word tokens and character 3-grams, hashing them
        into an L2-normalized 256-dimensional unit vector.
        """
        clean = " ".join(text.strip().lower().split())
        if not clean:
            return [0.0] * self.HASH_SPACE

        features = defaultdict(float)

        # 1. Semantic word tokens (weight = 2.5x)
        words = re.findall(r"[a-zA-Z0-9_\-\./]+", clean)
        for w in words:
            if len(w) > 1:
                features[f"w_{w}"] += 2.5

        # 2. Character 3-grams (weight = 1.0x)
        if len(clean) >= self.NGRAM_SIZE:
            for i in range(len(clean) - self.NGRAM_SIZE + 1):
                features[f"c_{clean[i:i + self.NGRAM_SIZE]}"] += 1.0
        else:
            features[f"c_{clean}"] += 1.0

        # Feature hashing into 256 buckets
        vector = [0.0] * self.HASH_SPACE
        for feat, weight in features.items():
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16) % self.HASH_SPACE
            vector[h] += weight

        # L2 Normalization (Unit vector projection)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > self.EPSILON:
            vector = [v / norm for v in vector]

        return vector

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two unit vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        return max(-1.0, min(1.0, dot))

    def _compute_semantic_velocity(self, v_curr: List[float], v_prev: List[float]) -> float:
        """
        Computes semantic velocity as 1 - cosine_similarity.
        - High velocity (> 0.7): Actions are semantically distinct (exploration / progress).
        - Low velocity (< 0.55): Actions are semantically gravitating around an attractor.
        """
        cos_sim = self._cosine_similarity(v_curr, v_prev)
        return max(0.0, 1.0 - cos_sim)

    def _discretize_action(self, vector: List[float]) -> int:
        """Projects continuous vector into a discrete 64-state space for Markov analysis."""
        indexed = heapq.nlargest(4, enumerate(vector), key=lambda x: x[1])
        state = sum((idx * (pos + 1)) for pos, (idx, val) in enumerate(indexed) if val > 0)
        return state % 64

    def _compute_markov_entropy(self, vectors: List[List[float]]) -> float:
        """
        Computes Shannon entropy of empirical Markov transition matrix:
        H(M) = -Σ_i Σ_j p_ij * log(p_ij)
        Low entropy indicates that the agent's actions are locked in a predictable attractor basin.
        """
        if len(vectors) < 3:
            return math.log(64)  # Theoretical maximum entropy for 64-state system (maximum uncertainty)

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

    def _is_exempt_action(self, action: str) -> bool:
        """
        Determines if an action is a viewport navigation primitive or an editor code modification.
        These operations are exempt from command-paraphrasing attractor detection and are
        governed by Tier 1 structural oscillation and active code refinement guards.
        """
        if not action:
            return True
        act_clean = action.strip().lower()

        # Check tool call wrapper (e.g. modify_file(path=...), str_replace_editor(...))
        tool_call_match = re.match(r"^([a-zA-Z0-9_]+)\s*\(", act_clean)
        if tool_call_match:
            tool_name = tool_call_match.group(1).lower()
            if any(m in tool_name for m in ("edit", "write", "patch", "replace", "create", "modify", "insert", "diff", "apply")):
                return True
            if any(nav in tool_name for nav in ("scroll", "goto", "cursor")):
                return True

        first_token = act_clean.split()[0] if act_clean else ""
        first_token = re.sub(r"[^a-zA-Z0-9_\-]", "", first_token)
        
        # 1. Viewport navigation commands
        if first_token in ("scroll_up", "scroll_down", "scroll", "page_up", "page_down", "goto", "cursor"):
            return True
        # 2. File modification primitives (including modern LLM tool call verbs)
        if first_token in (
            "edit", "write", "create", "replace", "patch",
            "modify_file", "edit_file", "write_file", "create_file", "str_replace_editor",
            "apply_diff", "apply_patch", "update_file", "insert_lines"
        ):
            return True
        return False

    def inspect_step(self, action: str, is_failing: bool = False) -> Tuple[bool, float, str]:
        """
        Inspects an agent action in the continuous dynamical semantic space.

        Returns:
            (is_attractor: bool, confidence: float, details_str: str)
        """
        if not action or not isinstance(action, str):
            return False, 0.0, ""

        # Exempt navigation primitives and code editing from command paraphrasing manifolds
        if self._is_exempt_action(action):
            return False, 0.0, ""

        vector = self._extract_feature_vector(action)
        self.action_history.append(action)
        self.vector_history.append(vector)
        self.failure_history.append(bool(is_failing))

        if len(self.vector_history) >= 2:
            velocity = self._compute_semantic_velocity(
                self.vector_history[-1],
                self.vector_history[-2]
            )
            self.velocity_history.append(velocity)
        else:
            return False, 0.0, ""

        # Need sufficient turns to verify stagnation
        if len(self.velocity_history) < self.stagnation_steps:
            return False, 0.0, ""

        # Axiom 1: A failure attractor cannot be declared on a turn that succeeded
        if not is_failing:
            return False, 0.0, ""

        # Axiom 2: Persistent failure across the window (majority of turns must be failing)
        recent_failures = list(self.failure_history)[-self.stagnation_steps:]
        min_required_failures = (self.stagnation_steps // 2) + 1
        if sum(recent_failures) < min_required_failures:
            return False, 0.0, ""

        # Axiom 3: If all recent actions in the window are literally identical strings, Tier 1 handles it
        if len(set(list(self.action_history)[-self.stagnation_steps - 1:])) <= 1:
            return False, 0.0, ""

        # 1. Metric 1: Mean & Variance of Semantic Velocity over recent window
        recent_velocities = list(self.velocity_history)[-self.stagnation_steps:]
        mean_vel = sum(recent_velocities) / len(recent_velocities)
        vel_variance = sum((v - mean_vel) ** 2 for v in recent_velocities) / len(recent_velocities)

        if mean_vel > self.velocity_threshold:
            # Semantic velocity is high: agent is exploring diverse strategies
            return False, 0.0, ""

        if vel_variance > self.variance_threshold:
            # High velocity variance indicates oscillating exploration, not a tight attractor basin
            return False, 0.0, ""

        # 2. Metric 2: Markov Transition Entropy
        entropy = self._compute_markov_entropy(list(self.vector_history))

        if entropy > self.entropy_threshold:
            # State space transitions remain diverse
            return False, 0.0, ""

        # 3. Attractor Basin Confirmed!
        self.total_attractors_detected += 1
        vel_score = max(0.0, 1.0 - (mean_vel / self.velocity_threshold))
        ent_score = max(0.0, 1.0 - (entropy / self.entropy_threshold))
        confidence = round(min(1.0, (vel_score * 0.6 + ent_score * 0.4)), 3)

        details = (
            f"Semantic attractor loop detected (mean velocity={mean_vel:.3f} < {self.velocity_threshold}, "
            f"variance={vel_variance:.4f} <= {self.variance_threshold}, "
            f"Markov entropy={entropy:.2f} < {self.entropy_threshold}, confidence={confidence:.1%})"
        )

        return True, confidence, details

    def reset(self):
        """Resets detector trajectory buffer."""
        self.action_history.clear()
        self.vector_history.clear()
        self.velocity_history.clear()
        self.failure_history.clear()
