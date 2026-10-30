"""
🦫 Capybala: Autonomous Agent Self-Healing & Deadlock-Resolution Runtime
Context-Aware Pruning for Yielding & Backtrack-Aligned Loop Avoidance
"""

# The Requests-Grade Core API (Clean, Zero-Magic)
from .api import watch, heal, validate, repair

# Core Engine
from .detector import DeadlockDetector, DeadlockEvent, DeadlockEmergencyStop
from .pruner import ContextPruner, PruneResult
from .healer import AgentHealer, HealingPrescription

# Proactive Engine, Adaptive Policy & Semantic Attractor Manifold
from .validator import SchemaValidator, repair_json_string
from .proactive import SearchOptimizer
from .policy import DeadlockPolicy, DeadlockMode
from .attractor import SemanticAttractorDetector

# Framework Integrations (Universal ABS Middleware)
from .integrations import (
    CapybalaLangGraphMiddleware,
    capybala_node,
    CapybalaCrewCallback,
    CapybalaAutoGenFilter,
)

# Legacy / Base Adapters
from .adapters import (
    BaseAgentAdapter,
    CapybalaGuard,
    LlamaStackCapybalaMiddleware,
    CapybalaCallbackHandler
)

__version__ = "0.8.0"
__all__ = [
    # Top-Level DX
    "watch",
    "heal",
    "validate",
    "repair",
    # Core Engine
    "DeadlockDetector",
    "DeadlockEvent",
    "DeadlockEmergencyStop",
    "ContextPruner",
    "PruneResult",
    "AgentHealer",
    "HealingPrescription",
    # Proactive, Adaptive & Manifold
    "SchemaValidator",
    "repair_json_string",
    "SearchOptimizer",
    "DeadlockPolicy",
    "DeadlockMode",
    "SemanticAttractorDetector",
    # Universal Integrations
    "CapybalaLangGraphMiddleware",
    "capybala_node",
    "CapybalaCrewCallback",
    "CapybalaAutoGenFilter",
    # Adapters
    "BaseAgentAdapter",
    "CapybalaGuard",
    "LlamaStackCapybalaMiddleware",
    "CapybalaCallbackHandler",
]
