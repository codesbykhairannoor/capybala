"""
Supervisor client interfaces for Capybala Doctor.
"""

from .supervisor import (
    BaseSupervisorClient,
    OpenRouterSupervisorClient,
    OllamaSupervisorClient,
    MockSupervisorClient
)

__all__ = [
    "BaseSupervisorClient",
    "OpenRouterSupervisorClient",
    "OllamaSupervisorClient",
    "MockSupervisorClient"
]

