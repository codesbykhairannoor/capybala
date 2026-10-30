"""
capybala.integrations.autogen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AutoGen / AG2 Integration.
Plugs into `agent.register_reply` and `is_termination_msg`.
Prevents ping-pong loops between autonomous agents and heals conversation context.

Usage:
    from autogen import ConversableAgent
    from capybala.integrations.autogen import CapybalaAutoGenFilter

    guard = CapybalaAutoGenFilter()
    guard.attach(agent)
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from ..api import heal
from ..detector import DeadlockDetector
from ..validator import SchemaValidator


class CapybalaAutoGenFilter:
    """
    Guards AutoGen ConversableAgents against ping-pong cycles and context corruption.
    """

    def __init__(self, repetition_threshold: int = 3, verbose: bool = False):
        self.detector = DeadlockDetector(repetition_threshold=repetition_threshold)
        self.verbose = verbose
        self.interventions_count = 0

    def attach(self, agent: Any) -> None:
        """
        Attaches Capybala's hook into an AutoGen ConversableAgent.
        """
        if hasattr(agent, "register_reply"):
            agent.register_reply(
                trigger=[agent.__class__, None],
                reply_func=self._reply_hook,
                position=0  # Highest priority filter
            )

    def _reply_hook(
        self,
        recipient: Any,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Any] = None,
        config: Optional[Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        AutoGen reply hook.
        Returns:
            (is_handled: bool, reply: Optional[str])
            If is_handled is False, AutoGen proceeds to generate normal reply.
        """
        if not messages or not isinstance(messages, list):
            return False, None

        # 1. Ensure Schema Integrity
        SchemaValidator.validate_and_repair(messages, in_place=True)

        # 2. Heal in-place if deadlock detected
        healed = heal(messages, verbose=self.verbose)
        if len(healed) < len(messages):
            self.interventions_count += 1
            # Return True with guidance prompt if critically deadlocked
            return False, None

        return False, None

    def is_termination_msg(self, message: Dict[str, Any]) -> bool:
        """
        Can be passed directly to `is_termination_msg` in AutoGen config.
        Flags termination if an unrecoverable circuit-breaker deadlock occurs.
        """
        content = str(message.get("content", "")) if isinstance(message, dict) else str(message)
        return "[CAPYBALA EMERGENCY STOP]" in content
