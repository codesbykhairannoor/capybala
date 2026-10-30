"""
capybala.adapters.langchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~
LangChain & LangGraph integration for Capybala.
Provides a drop-in CallbackHandler that tracks tool loops and alerts/heals agents.
"""

from typing import Dict, Any, List, Optional
from .base import BaseAgentAdapter
from ..healer import HealingPrescription

# Optional duck-typed inheritance from langchain_core if installed
try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ImportError:
    class BaseCallbackHandler:  # type: ignore
        """Fallback base class when langchain is not installed."""
        pass


class CapybalaCallbackHandler(BaseCallbackHandler, BaseAgentAdapter):
    """
    Drop-in LangChain CallbackHandler that watches tool calls for cognitive deadlocks.
    Usage:
        agent_executor = create_react_agent(..., callbacks=[CapybalaCallbackHandler()])
    """

    def __init__(
        self,
        repetition_threshold: int = 3,
        supervisor_model: str = "meta-llama/llama-3.2-1b-instruct",
        use_supervisor_llm: bool = False,
    ):
        BaseCallbackHandler.__init__(self)
        BaseAgentAdapter.__init__(
            self,
            repetition_threshold=repetition_threshold,
            supervisor_model=supervisor_model,
            use_supervisor_llm=use_supervisor_llm,
        )
        self.last_action_name: str = ""
        self.last_action_input: str = ""
        self.deadlock_triggered: bool = False
        self.last_prescription: Optional[HealingPrescription] = None

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a LangChain tool starts running."""
        self.last_action_name = serialized.get("name", "tool")
        self.last_action_input = str(input_str)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a LangChain tool finishes running."""
        action = f"{self.last_action_name}: {self.last_action_input}"
        event = self.detector.check(action, str(output))

        if event.is_deadlock:
            self.deadlock_triggered = True
            rx = self.healer.prescribe(
                deadlock_pattern=event.pattern_type or "tool_loop",
                failing_action=action,
                error_signature=str(output)
            )
            self.last_prescription = rx

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a LangChain tool encounters an unhandled exception."""
        action = f"{self.last_action_name}: {self.last_action_input}"
        event = self.detector.check(action, f"{type(error).__name__}: {str(error)}")

        if event.is_deadlock:
            self.deadlock_triggered = True
            rx = self.healer.prescribe(
                deadlock_pattern=event.pattern_type or "tool_error_loop",
                failing_action=action,
                error_signature=str(error)
            )
            self.last_prescription = rx

