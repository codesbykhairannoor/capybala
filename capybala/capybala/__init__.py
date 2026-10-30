"""
🦫 Capybala: Autonomous Agent Self-Healing & Deadlock-Resolution Runtime
Context-Aware Pruning for Yielding & Backtrack-Aligned Loop Avoidance
"""

# The Requests-Grade Core API (Clean, Zero-Magic)
from .api import watch, heal, validate

# Core Components
from .detector import DeadlockDetector, DeadlockEvent
from .pruner import ContextPruner, PruneResult
from .healer import AgentHealer, HealingPrescription

# Optional Framework Adapters
from .adapters import (
    BaseAgentAdapter,
    CapybalaGuard,
    LlamaStackCapybalaMiddleware,
    CapybalaCallbackHandler
)

__version__ = "0.3.0"
__all__ = [
    # Top-Level DX
    "watch",
    "heal",
    "validate",
    # Core Engine
    "DeadlockDetector",
    "DeadlockEvent",
    "ContextPruner",
    "PruneResult",
    "AgentHealer",
    "HealingPrescription",
    # Adapters
    "BaseAgentAdapter",
    "CapybalaGuard",
    "LlamaStackCapybalaMiddleware",
    "CapybalaCallbackHandler",
]
