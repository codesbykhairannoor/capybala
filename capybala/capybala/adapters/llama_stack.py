"""
capybala.adapters.llama_stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Native Meta Llama Stack Agent Middleware.
Seamlessly integrates with Llama Stack Agent sessions, intercepting runaway
tool loops and pruning context windows on Llama-3.1-70B/405B agents using
an out-of-band Llama-3.2-1B/3B supervisor.
"""

from typing import List, Dict, Any, Optional, Tuple
from .base import BaseAgentAdapter
from ..healer import HealingPrescription


class LlamaStackCapybalaMiddleware(BaseAgentAdapter):
    """
    Middleware for Meta Llama Stack Agent runtimes.
    Can be used as a turn interceptor in Llama Stack Agent loops.
    """

    def __init__(
        self,
        repetition_threshold: int = 3,
        supervisor_model: str = "meta-llama/llama-3.2-1b-instruct",
        supervisor_client: Optional[Any] = None,
        use_supervisor_llm: bool = False,
    ):
        super().__init__(
            repetition_threshold=repetition_threshold,
            supervisor_model=supervisor_model,
            supervisor_client=supervisor_client,
            use_supervisor_llm=use_supervisor_llm,
        )

    def on_tool_step(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_output: str,
        session_turns: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], Optional[HealingPrescription]]:
        """
        Intercepts a Llama Stack tool execution step.

        Parameters:
        - tool_name: Name of tool called (e.g. 'execute_code', 'terminal')
        - tool_arguments: Dict of arguments passed to tool
        - tool_output: The environment response or stdout/stderr
        - session_turns: Llama Stack message list for current agent session

        Returns:
        - (is_deadlocked, rescued_turns, optional_prescription)
        """
        # Create a canonical representation of the action
        action_signature = f"{tool_name}({tool_arguments})"

        return self.intercept_step(
            action=action_signature,
            observation=tool_output,
            messages=session_turns
        )

    def wrap_turn_request(self, agent_client: Any, session_id: str, turn_request: Dict[str, Any]) -> Any:
        """
        Helper method to wrap a Llama Stack client agent.turn.create call.
        """
        # Standalone pass-through hook for Llama Stack client integration
        return agent_client.agents.turn.create(
            session_id=session_id,
            **turn_request
        )

