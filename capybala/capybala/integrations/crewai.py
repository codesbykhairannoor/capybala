"""
capybala.integrations.crewai
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CrewAI Step & Task Callback Integration.
Plugs directly into `Agent(step_callback=...)` or `Crew(task_callback=...)`.
Detects repetitive tool invocations, oscillating commands, and prunes fruitless search storms.

Usage:
    from crewai import Agent
    from capybala.integrations.crewai import CapybalaCrewCallback

    cb = CapybalaCrewCallback()
    agent = Agent(
        role="Coder",
        goal="Solve bug",
        step_callback=cb
    )
"""

from typing import Any, Optional, Dict, List
from ..detector import DeadlockDetector
from ..proactive import SearchOptimizer


class CapybalaCrewCallback:
    """
    Step callback for CrewAI agents.
    Tracks tool use per step and triggers graceful backtracking on deadlocks.
    """

    def __init__(
        self,
        repetition_threshold: int = 3,
        enable_proactive_hints: bool = True,
        verbose: bool = False
    ):
        self.detector = DeadlockDetector(repetition_threshold=repetition_threshold)
        self.search_optimizer = SearchOptimizer() if enable_proactive_hints else None
        self.verbose = verbose
        self.interventions_count = 0
        self.last_deadlock: Optional[Dict[str, Any]] = None

    def __call__(self, step_output: Any) -> None:
        """
        Invoked by CrewAI after every agent thought/tool step.
        Supports both raw dictionaries and CrewAI AgentAction / AgentFinish objects.
        """
        action_str = ""
        obs_str = ""

        # Handle object or dict
        if hasattr(step_output, "tool") and hasattr(step_output, "tool_input"):
            action_str = f"{step_output.tool}({step_output.tool_input})"
            obs_str = str(getattr(step_output, "result", ""))
        elif isinstance(step_output, dict):
            action_str = str(step_output.get("action", step_output.get("tool", "")))
            obs_str = str(step_output.get("observation", step_output.get("result", "")))
        else:
            action_str = str(step_output)

        if not action_str:
            return

        # 1. Proactive Search Optimization
        if self.search_optimizer:
            should_hint, hint = self.search_optimizer.inspect_step(action_str, obs_str)
            if should_hint and hasattr(step_output, "result"):
                step_output.result = f"{step_output.result}\n\n{hint}"

        # 2. Deadlock Detection
        event = self.detector.check(action_str, obs_str)
        if event.is_deadlock:
            self.interventions_count += 1
            self.last_deadlock = {
                "pattern": event.pattern_type,
                "details": event.details,
                "action": action_str,
            }
            if self.verbose:
                print(f"[Capybala CrewAI Guard] Intercepted deadlock: {event.pattern_type} on '{action_str[:50]}'")

