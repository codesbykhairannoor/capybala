"""
capybala.adapters.generic
~~~~~~~~~~~~~~~~~~~~~~~~~
Generic adapter for raw message lists, OpenAI API, Anthropic, Ollama, and custom agent loops.
Provides both an object wrapper (`CapybalaGuard`) and a decorator (`@capybala_watch`).
"""

import functools
from typing import List, Dict, Any, Optional, Callable
from .base import BaseAgentAdapter
from ..healer import HealingPrescription


class CapybalaGuard(BaseAgentAdapter):
    """
    Lightweight runtime guard wrapping an agent's active conversation messages.
    """

    def __init__(
        self,
        messages: List[Dict[str, Any]],
        task_prompt: str = "",
        repetition_threshold: int = 3,
        oscillation_threshold: int = 2,
        supervisor_model: str = "meta-llama/llama-3.2-1b-instruct",
        supervisor_client: Optional[Any] = None,
        use_supervisor_llm: bool = False,
    ):
        super().__init__(
            repetition_threshold=repetition_threshold,
            oscillation_threshold=oscillation_threshold,
            supervisor_model=supervisor_model,
            supervisor_client=supervisor_client,
            use_supervisor_llm=use_supervisor_llm,
        )
        self.messages = messages
        self.task_prompt = task_prompt
        self.latest_prescription: Optional[HealingPrescription] = None
        self.is_deadlocked: bool = False

    def step(self, action: str, observation: str) -> bool:
        """
        Record an action and observation turn.
        If a deadlock is identified, self-heals in-place and updates `self.messages`.

        Returns:
        - True if a deadlock was intercepted and healed, False otherwise.
        """
        is_rescued, updated_msgs, rx = self.intercept_step(
            action=action,
            observation=observation,
            messages=self.messages,
            task_prompt=self.task_prompt
        )

        if is_rescued:
            self.messages.clear()
            self.messages.extend(updated_msgs)
            self.latest_prescription = rx
            self.is_deadlocked = True
            return True

        self.is_deadlocked = False
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def capybala_watch(
    repetition_threshold: int = 3,
    use_supervisor_llm: bool = False,
    supervisor_model: str = "meta-llama/llama-3.2-1b-instruct"
):
    """
    Function decorator to automatically attach Capybala deadlock detection
    and self-healing to an autonomous agent step function.
    """
    def decorator(func: Callable):
        adapter = BaseAgentAdapter(
            repetition_threshold=repetition_threshold,
            use_supervisor_llm=use_supervisor_llm,
            supervisor_model=supervisor_model
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Expecting kwargs or args containing 'action', 'observation', and 'messages'
            action = kwargs.get("action", "")
            observation = kwargs.get("observation", "")
            messages = kwargs.get("messages", None)

            if messages is not None and action:
                rescued, updated_msgs, rx = adapter.intercept_step(
                    action=action,
                    observation=observation,
                    messages=messages
                )
                if rescued:
                    kwargs["messages"] = updated_msgs
                    kwargs["capybala_healed"] = True
                    kwargs["prescription"] = rx

            return func(*args, **kwargs)
        return wrapper
    return decorator

