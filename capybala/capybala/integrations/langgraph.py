"""
capybala.integrations.langgraph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LangGraph & LangChain StateGraph Middleware.
Drop-in wrapper for LangGraph agent nodes. Prevents infinite recursion,
heals loops in-place, and eliminates 400 Bad Request tool errors.

Usage:
    from capybala.integrations.langgraph import capybala_node

    @capybala_node
    def agent_node(state):
        # Your normal LangGraph node logic
        return {"messages": [response]}
"""

import functools
from typing import Dict, Any, Callable, Optional
from ..api import heal
from ..validator import SchemaValidator


def capybala_node(node_fn: Callable) -> Callable:
    """
    Decorator for LangGraph nodes.
    Inspects and heals state['messages'] in-place before and after node execution.
    """
    @functools.wraps(node_fn)
    def wrapper(state: Dict[str, Any], *args, **kwargs) -> Any:
        if isinstance(state, dict) and "messages" in state:
            messages = state["messages"]
            if isinstance(messages, list):
                # 1. Proactive schema validation
                SchemaValidator.validate_and_repair(messages, in_place=True)
                # 2. Heuristic loop detection and context healing
                heal(messages, verbose=False)

        res = node_fn(state, *args, **kwargs)

        # After execution, ensure outgoing messages are clean
        if isinstance(res, dict) and "messages" in res:
            res_msgs = res["messages"]
            if isinstance(res_msgs, list):
                SchemaValidator.validate_and_repair(res_msgs, in_place=True)

        return res

    return wrapper


class CapybalaLangGraphMiddleware:
    """
    Class-based middleware for LangGraph workflows.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def intercept(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a LangGraph state dictionary, ensuring zero deadlocks and zero 400 errors.
        """
        if isinstance(state, dict) and "messages" in state:
            msgs = state["messages"]
            if isinstance(msgs, list):
                SchemaValidator.validate_and_repair(msgs, in_place=True)
                heal(msgs, verbose=self.verbose)
        return state

