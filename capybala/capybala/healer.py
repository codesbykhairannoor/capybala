"""
capybala.healer
~~~~~~~~~~~~~~~
Strategic Guidance & Reflection Synthesis.
Avoids autoregressive negative priming (Pink Elephant Effect) by providing
constructive, forward-looking debugging directives mapped to error taxonomies.
Includes Progressive Escalation to prevent autoregressive reflection echo traps.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class HealingPrescription:
    diagnosis: str
    recommended_pivot: str
    injected_message: Dict[str, str]
    mode_used: str
    tokens_used: int = 0
    escalation_level: int = 1


class AgentHealer:
    """
    Synthesizes actionable, positive forward directives without negative priming traps.
    Supports multi-level progressive escalation to break persistent cognitive deadlocks.
    """

    def __init__(
        self,
        supervisor_client: Optional[Any] = None,
        supervisor_model: str = "meta-llama/llama-3.2-1b-instruct"
    ):
        self.supervisor_client = supervisor_client
        self.supervisor_model = supervisor_model

    def _generate_heuristic_pivot(
        self,
        error_signature: str,
        pattern_type: str,
        failing_action: str,
        escalation_level: int = 1
    ) -> str:
        """
        Constructive forward guidance mapped to failure taxonomies.
        Progressively escalates guidance if previous interventions failed.
        """
        err_lower = (error_signature or "").lower()

        # Base category advice
        if pattern_type == "oscillation":
            base = (
                "An alternating cycle between conflicting actions was detected.\n"
                "1. Discard both alternating options.\n"
                "2. Step back and formulate a third, completely new hypothesis.\n"
                "3. Re-examine the original issue prompt for missed constraints."
            )
        elif pattern_type == "fuzzy_repetition":
            base = (
                f"Polymorphic action repetition detected for '{failing_action[:60]}'.\n"
                "1. Stop tweaking flags, parameters, or superficial argument variations of this command.\n"
                "2. The underlying premise of this tool/command invocation is failing.\n"
                "3. Pivot completely to an alternative approach or inspect prerequisite dependencies."
            )
        elif pattern_type == "delegation_cycle":
            base = (
                "A multi-agent delegation cycle (ping-pong handoff) was detected.\n"
                "1. Do NOT delegate or hand off this task to another agent again.\n"
                "2. Take decisive local ownership and execute the required action directly.\n"
                "3. If missing information, inspect the environment or state yourself instead of delegating."
            )
        elif pattern_type == "output_stagnation":
            base = (
                "Environment feedback is completely stagnant despite varied command attempts.\n"
                "1. Stop executing commands that produce the same static failure state.\n"
                "2. Inspect the environment prerequisites (running services, network ports, installed packages).\n"
                "3. Verify that previous modifications were actually applied and saved."
            )
        elif "importerror" in err_lower or "modulenotfounderror" in err_lower:
            base = (
                "The current import path or dependency is unresolved.\n"
                "1. Inspect sys.path, setup.py, or pyproject.toml to confirm root package boundaries.\n"
                "2. Verify whether local virtualenv packages require editable installation (pip install -e .).\n"
                "3. Pivot to inspecting the module directory structure directly."
            )
        elif "syntaxerror" in err_lower:
            base = (
                "A syntax / AST parse error was encountered.\n"
                "1. Re-read the modified source file around the indicated lines.\n"
                "2. Inspect unclosed brackets, indentation, or Python version grammar.\n"
                "3. Verify file syntax locally before executing test scripts."
            )
        elif "assertionerror" in err_lower or "failed" in err_lower:
            base = (
                "Target test assertions failed under the current patch.\n"
                "1. Formulate a new hypothesis targeting the core logic, not the test harness.\n"
                "2. Inspect edge cases (None values, type mismatches, empty collections).\n"
                "3. Trace intermediate variables to diagnose the root assertion discrepancy."
            )
        elif "filenotfounderror" in err_lower or "no such file" in err_lower:
            base = (
                "Target path does not exist.\n"
                "1. Run directory listing (ls or find) from root to confirm relative path.\n"
                "2. Align working directory assumptions with the actual repository structure."
            )
        else:
            base = (
                f"Action '{failing_action[:60]}' yielded repetitive un-actionable feedback.\n"
                "1. Abandon this specific line of inquiry.\n"
                "2. Broaden your diagnostic scope to alternative modules or configuration files."
            )

        # Progressive escalation for repeated failures
        if escalation_level >= 3:
            escalation_prefix = (
                f"⚠️ [CRITICAL ESCALATION - Level {escalation_level}]: "
                "Multiple consecutive recovery attempts have failed. "
                "Do NOT make further micro-edits. Discard the current line of modifications entirely. "
                "Construct a minimal independent verification script to test your fundamental assumption.\n\n"
            )
            return escalation_prefix + base

        return base

    def prescribe(
        self,
        deadlock_pattern: str,
        failing_action: str,
        error_signature: str = "",
        task_prompt: str = "",
        use_supervisor_llm: bool = False,
        target_provider: str = "auto",
        escalation_level: int = 1
    ) -> HealingPrescription:
        """
        Generates a forward-looking prescription for the agent.
        Uses role: 'user' to ensure strict provider schema compatibility
        across Anthropic, Mistral, and Llama-3 without mid-stream system prompt errors.
        """
        diagnosis = (
            f"Cognitive Deadlock [{deadlock_pattern.upper()}]: "
            f"Action '{failing_action[:65]}' encountered persistent failure: {error_signature[:75]}."
        )

        pivot_advice = self._generate_heuristic_pivot(
            error_signature, deadlock_pattern, failing_action, escalation_level=escalation_level
        )
        mode = "heuristic"
        tokens_cost = 0

        if use_supervisor_llm and self.supervisor_client:
            try:
                prompt = (
                    f"Cognitive Deadlock [{deadlock_pattern}]: Action '{failing_action}' failed with '{error_signature}'. "
                    f"Task prompt: '{task_prompt}'. Escalation level: {escalation_level}. "
                    "Suggest a concise, constructive pivot hypothesis."
                )
                pivot_advice = self.supervisor_client.generate(self.supervisor_model, prompt)
                mode = "supervisor_llm"
            except Exception:
                pass

        # Constructive directive without 'Pink Elephant' negative constraint
        doctor_directive = (
            f"[🦫 CAPYBALA DOCTOR INTERVENTION]\n"
            f"DIAGNOSIS: {diagnosis}\n"
            f"History has been atomically rolled back to a clean state.\n\n"
            f"RECOMMENDED STRATEGIC PIVOT:\n"
            f"{pivot_advice}\n\n"
            f"Proceed with your alternative hypothesis now."
        )

        injected_msg = {
            "role": "user",
            "content": doctor_directive
        }

        return HealingPrescription(
            diagnosis=diagnosis,
            recommended_pivot=pivot_advice,
            injected_message=injected_msg,
            mode_used=mode,
            tokens_used=tokens_cost,
            escalation_level=escalation_level
        )
