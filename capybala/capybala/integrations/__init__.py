"""
capybala.integrations
~~~~~~~~~~~~~~~~~~~~~
Universal Drop-in Middleware Integrations for Leading Agent Frameworks:
- LangGraph & LangChain: State-graph node wrapper & CallbackHandler.
- CrewAI: Step & Task Callback for agent execution loops.
- AutoGen / AG2: Reply hook & termination guard.
"""

from .langgraph import CapybalaLangGraphMiddleware, capybala_node
from .crewai import CapybalaCrewCallback
from .autogen import CapybalaAutoGenFilter

__all__ = [
    "CapybalaLangGraphMiddleware",
    "capybala_node",
    "CapybalaCrewCallback",
    "CapybalaAutoGenFilter",
]
