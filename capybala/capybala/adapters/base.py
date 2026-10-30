"""
capybala.adapters.base
~~~~~~~~~~~~~~~~~~~~~~
Abstract Base Adapter for universal agent framework integration.
Combines Detector, Pruner, and Healer into a unified lifecycle interceptor.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from ..detector import DeadlockDetector, DeadlockEvent
from ..pruner import ContextPruner, PruneResult
from ..healer import AgentHealer, HealingPrescription


class BaseAgentAdapter(ABC):
    """
    Base lifecycle adapter connecting Capybala to any AI agent runtime.
    """

    def __init__(
        self,
        repetition_threshold: int = 3,
        oscillation_threshold: int = 2,
        supervisor_model: str = "meta-llama/llama-3.2-1b-instruct",
        supervisor_client: Optional[Any] = None,
        use_supervisor_llm: bool = False,
    ):
        self.detector = DeadlockDetector(
            repetition_threshold=repetition_threshold,
            oscillation_threshold=oscillation_threshold
        )
        self.pruner = ContextPruner()
        self.healer = AgentHealer(
            supervisor_client=supervisor_client,
            supervisor_model=supervisor_model
        )
        self.use_supervisor_llm = use_supervisor_llm
        self.interventions_count = 0
        self.total_tokens_recovered = 0

    def intercept_step(
        self,
        action: str,
        observation: str,
        messages: List[Dict[str, Any]],
        task_prompt: str = ""
    ) -> Tuple[bool, List[Dict[str, Any]], Optional[HealingPrescription]]:
        """
        Intercepts an agent's execution step.

        Parameters:
        - action: The tool call or terminal command the agent executed.
        - observation: The environment response / traceback output.
        - messages: The running conversation history.
        - task_prompt: The initial objective description.

        Returns:
        - (is_rescued, updated_messages, optional_prescription)
        """
        event = self.detector.check(action, observation)

        if not event.is_deadlock:
            return False, messages, None

        # Deadlock detected! Execute Capybala self-healing protocol:
        self.interventions_count += 1

        # 1. Formulate strategic Doctor Prescription
        rx = self.healer.prescribe(
            deadlock_pattern=event.pattern_type or "unknown",
            failing_action=action,
            error_signature=observation,
            task_prompt=task_prompt,
            use_supervisor_llm=self.use_supervisor_llm
        )

        # 2. Execute Atomic Checkpoint Rollback with Domain Guidance
        prune_result = self.pruner.rollback_and_reflect(
            messages=messages,
            failing_action=action,
            deadlock_details=event.details,
            reflection_guidance=rx.recommended_pivot,
            rollback_turns=event.repetition_count * 2
        )
        self.total_tokens_recovered += prune_result.tokens_saved_estimate

        return True, prune_result.pruned_messages, rx

    def reset(self):
        """Resets detector state for a new conversation turn."""
        self.detector.reset()

