"""Result Synthesizer — stitches step outputs into a coherent final result.

After all steps complete, the synthesizer:
1. Checks for a playbook-defined synthesis step and runs it via an LLM.
2. Formats all artifacts into a summary report.
3. Returns a ``SynthesisResult`` with the complete output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from modules.orchestrator.decomposer import Step
    from modules.orchestrator.executor import ExecutionState, StepOutcome
    from modules.orchestrator.tools.base import Tool

logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    """Final output of an orchestration run.

    Attributes:
        success: True if all required steps completed without error.
        summary: Human-readable summary of what was produced.
        artifacts: All named outputs from the run (key → value).
        total_cost: Accumulated cost in USD.
        step_count: Total steps executed.
        failed_steps: Names of steps that failed.
        synthesis_output: Output from the optional synthesis LLM step.
    """

    success: bool
    summary: str = ""
    artifacts: Dict[str, Any] = field(default_factory=dict)
    total_cost: float = 0.0
    step_count: int = 0
    failed_steps: List[str] = field(default_factory=list)
    synthesis_output: Optional[str] = None


class ResultSynthesizer:
    """Assembles the final SynthesisResult from an ExecutionState.

    Optionally runs a synthesis LLM step to produce a coherent summary
    that references all step outputs (e.g. a cross-cutting code review).

    Args:
        tool: Optional LLMTool instance for running the synthesis step.
    """

    def __init__(self, tool: Optional["Tool"] = None) -> None:
        self.tool = tool

    def synthesize(
        self,
        state: "ExecutionState",
        synthesis_step: Optional["Step"] = None,
    ) -> SynthesisResult:
        """Build a SynthesisResult from the completed execution state.

        Args:
            state: Completed ExecutionState from StepExecutor.
            synthesis_step: Optional Step to run as a final coherence check.
        """
        failed = list(state.failed)
        all_artifacts = dict(state.context)

        synthesis_output: Optional[str] = None
        if synthesis_step is not None and self.tool is not None:
            synthesis_output = self._run_synthesis(synthesis_step, state)

        summary = self._build_summary(state, synthesis_output)

        return SynthesisResult(
            success=state.success,
            summary=summary,
            artifacts=all_artifacts,
            total_cost=state.total_cost,
            step_count=len(state.outcomes),
            failed_steps=failed,
            synthesis_output=synthesis_output,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_synthesis(
        self, synthesis_step: "Step", state: "ExecutionState"
    ) -> Optional[str]:
        """Run the synthesis LLM step, injecting all artifacts as context."""
        if self.tool is None:
            return None

        task = synthesis_step.to_task_dict()
        try:
            result = self.tool.execute(task, state.context)
            if result.success:
                return result.output
            logger.warning("Synthesis step failed: %s", result.error)
        except Exception:
            logger.exception("Error during synthesis step")
        return None

    def _build_summary(
        self, state: "ExecutionState", synthesis_output: Optional[str]
    ) -> str:
        """Build a plain-text summary of the run."""
        lines: List[str] = []

        if synthesis_output:
            lines.append(synthesis_output)
            lines.append("")

        if state.failed:
            lines.append(f"WARNING: {len(state.failed)} step(s) failed: {', '.join(sorted(state.failed))}")
        else:
            lines.append(f"All {len(state.completed)} steps completed successfully.")

        lines.append(f"Total cost: ${state.total_cost:.4f}")

        artifact_names = [k for k in state.context if not k.startswith("_")]
        if artifact_names:
            lines.append(f"Artifacts: {', '.join(sorted(artifact_names))}")

        return "\n".join(lines)
