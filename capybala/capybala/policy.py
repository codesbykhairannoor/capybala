"""
capybala.policy
~~~~~~~~~~~~~~~
Adaptive Deadlock Policy Engine.
Dynamically tunes detection thresholds based on agent execution lifecycle:
- Exploration Mode: High tolerance for reading, browsing, and discovery.
- Refinement Mode: Strict, zero-tolerance thresholds for code editing and test failures.
- Adaptive Mode (Default): Dynamically transitions from Exploration to Refinement
  as soon as mutating or execution actions occur.
"""

from enum import Enum
from typing import Dict, Any, Optional
import re


class DeadlockMode(str, Enum):
    EXPLORATION = "exploration"
    REFINEMENT = "refinement"
    ADAPTIVE = "adaptive"


MUTATING_ACTION_PATTERN = re.compile(
    r"(?:^|[\W_])(?:edit|editor|patch|replace|write|create|rm|del|mkdir|touch|cp|mv|pytest|unittest|python\s+test)(?:[\W_]|$)",
    re.IGNORECASE
)


class DeadlockPolicy:
    """
    Manages dynamic sensitivity thresholds for agent runtime supervision.
    Prevents false alarms during exploratory code browsing while ensuring
    sub-second interception once active code editing begins.
    """

    def __init__(self, mode: DeadlockMode = DeadlockMode.ADAPTIVE):
        self.mode = mode
        self.current_phase = DeadlockMode.EXPLORATION if mode == DeadlockMode.ADAPTIVE else mode
        self.mutating_actions_seen = 0
        self.total_actions_evaluated = 0

    def update_action(self, action: str):
        """Updates lifecycle phase based on observed action."""
        self.total_actions_evaluated += 1
        if not action or not isinstance(action, str):
            return

        if MUTATING_ACTION_PATTERN.search(action):
            self.mutating_actions_seen += 1
            if self.mode == DeadlockMode.ADAPTIVE:
                self.current_phase = DeadlockMode.REFINEMENT

    def get_thresholds(self) -> Dict[str, Any]:
        """
        Returns dynamic thresholds matching the active phase.
        """
        if self.current_phase == DeadlockMode.EXPLORATION:
            return {
                "repetition_threshold": 4,
                "oscillation_threshold": 3,
                "error_threshold": 4,
                "max_exploration_depth": 20,
                "phase": "exploration"
            }
        else:  # REFINEMENT
            return {
                "repetition_threshold": 2,
                "oscillation_threshold": 2,
                "error_threshold": 2,
                "max_exploration_depth": 10,
                "phase": "refinement"
            }

    def is_in_refinement(self) -> bool:
        """True if the policy is currently enforcing strict refinement thresholds."""
        return self.current_phase == DeadlockMode.REFINEMENT

