"""
capybala.proactive
~~~~~~~~~~~~~~~~~~
Proactive Search Optimizer & Early Nudge Interceptor.
Catches fruitless grep storms and dead search loops at turn 4 instead of turn 15,
proactively guiding agents before they burn dozens of wasteful API turns.
"""

import re
from typing import Optional, Tuple, Dict, Any, List


EMPTY_SEARCH_INDICATORS = (
    "no matches found",
    "0 matches",
    "pattern not found",
    "no such file or directory",
    "cannot access",
    "nothing found",
    "total 0",
    "empty list",
    "[]",
    "none found",
)

SEARCH_COMMAND_VERBS = (
    "grep", "find", "find_file", "search_dir", "search", "locate", "ag", "rg", "ack"
)


class SearchOptimizer:
    """
    Tracks and optimizes search patterns during agent execution.
    Detects unguided search thrashing early (threshold = 4) and provides
    proactive guidance hints to redirect the agent towards productive discovery.
    """

    def __init__(self, empty_search_threshold: int = 4):
        self.empty_search_threshold = empty_search_threshold
        self.consecutive_empty_searches = 0
        self.last_search_terms: List[str] = []
        self.total_hints_injected = 0

    def is_search_action(self, action: str) -> bool:
        """Determines if the action is a search or discovery command."""
        if not action or not isinstance(action, str):
            return False
        clean = action.strip().lower()
        # Direct command prefix
        for verb in SEARCH_COMMAND_VERBS:
            if re.search(rf"(?:^|[\s_`\"'])({verb})(?:[\s_`\"'\(]|$)", clean):
                return True
        return False

    def is_empty_observation(self, observation: str) -> bool:
        """Checks if the tool output indicates an empty or fruitless search result."""
        if not observation or not isinstance(observation, str):
            return True
        obs = observation.strip().lower()
        if len(obs) == 0:
            return True
        # Check explicit empty indicators
        for ind in EMPTY_SEARCH_INDICATORS:
            if ind in obs:
                return True
        # Very short non-informative output (e.g. just a newline or exit code 0/1 with no lines)
        if len(obs) < 15 and ("error" not in obs and "found" not in obs):
            return True
        return False

    def inspect_step(self, action: str, observation: str) -> Tuple[bool, Optional[str]]:
        """
        Inspects an agent action and observation.
        Returns:
            (should_inject_hint: bool, proactive_hint_str: Optional[str])
        """
        if self.is_search_action(action):
            if self.is_empty_observation(observation):
                self.consecutive_empty_searches += 1
                if self.consecutive_empty_searches >= self.empty_search_threshold:
                    self.total_hints_injected += 1
                    hint = (
                        f"[Capybala Proactive Guidance]: {self.consecutive_empty_searches} consecutive searches yielded no matches. "
                        "Suggestions: 1) Verify path exists using directory listing ('ls -la'), "
                        "2) Use case-insensitive search ('grep -i' / 'rg -i'), "
                        "3) Broaden search pattern or check root module '__init__.py'."
                    )
                    return True, hint
            else:
                # Search returned productive results! Reset counter
                self.consecutive_empty_searches = 0
        else:
            # Agent pivoted to reading a specific file or mutating code -> reset
            self.consecutive_empty_searches = 0

        return False, None

    def annotate_observation_if_needed(self, action: str, observation: str) -> str:
        """
        Wraps observation with proactive advice if search thrashing is detected.
        """
        should_inject, hint = self.inspect_step(action, observation)
        if should_inject and hint:
            return observation.rstrip() + "\n\n" + hint
        return observation
