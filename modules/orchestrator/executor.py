"""Step Executor — runs workflow steps with dependency-aware scheduling.

Resolves the dependency DAG among steps and executes them in valid
topological order. Independent steps that have no unresolved dependencies
are eligible to run immediately; execution is currently sequential but
the design supports future parallel scheduling.

State is maintained in an ``ExecutionState`` object that tracks completed
step outputs, accumulated cost, and any errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging
import time

if TYPE_CHECKING:
    from modules.orchestrator.decomposer import Step
    from modules.orchestrator.tools.base import Tool

logger = logging.getLogger(__name__)


@dataclass
class StepOutcome:
    """Result of executing a single step.

    Attributes:
        step_name: Name of the step.
        success: Whether the step succeeded.
        output: The step's primary output value.
        artifacts: Named outputs available to downstream steps.
        cost: Cost incurred by this step (USD).
        duration_ms: Wall-clock time in milliseconds.
        error: Error message if not successful.
    """

    step_name: str
    success: bool
    output: Any = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class ExecutionState:
    """Mutable state of an in-progress orchestration run.

    Attributes:
        context: Accumulated artifact key → value mapping.
        outcomes: Per-step execution results.
        total_cost: Running cost total.
        completed: Set of step names that finished successfully.
        failed: Set of step names that failed.
    """

    context: Dict[str, Any] = field(default_factory=dict)
    outcomes: List[StepOutcome] = field(default_factory=list)
    total_cost: float = 0.0
    completed: set = field(default_factory=set)
    failed: set = field(default_factory=set)

    def record(self, outcome: StepOutcome) -> None:
        self.outcomes.append(outcome)
        self.total_cost += outcome.cost
        if outcome.success:
            self.completed.add(outcome.step_name)
            self.context.update(outcome.artifacts)
        else:
            self.failed.add(outcome.step_name)

    @property
    def success(self) -> bool:
        return len(self.failed) == 0

    def summary(self) -> Dict[str, Any]:
        return {
            "steps_completed": len(self.completed),
            "steps_failed": len(self.failed),
            "total_cost": self.total_cost,
            "success": self.success,
        }


class StepExecutor:
    """Executes workflow steps using registered tools.

    Tools are registered with ``register_tool``. Before each step runs,
    the executor selects the cheapest capable tool. If no tool can handle
    the step it is skipped with a failure outcome.

    Dependency resolution ensures a step only runs when all steps in
    ``depends_on`` have completed successfully.

    Args:
        on_step_start: Optional callback(step_name, step_index, total).
        on_step_done: Optional callback(outcome).
    """

    def __init__(
        self,
        on_step_start: Any = None,
        on_step_done: Any = None,
    ) -> None:
        self._tools: List["Tool"] = []
        self.on_step_start = on_step_start
        self.on_step_done = on_step_done

    def register_tool(self, tool: "Tool") -> None:
        """Add a tool to the executor's registry."""
        self._tools.append(tool)

    def execute_all(self, steps: List["Step"]) -> ExecutionState:
        """Run all steps in dependency order, returning final state.

        Steps whose dependencies fail are skipped (recorded as failures).
        """
        state = ExecutionState()
        remaining = list(steps)
        total = len(remaining)
        step_index = 0

        while remaining:
            ready = self._find_ready(remaining, state)
            if not ready:
                # Circular dependency or all remaining depend on failed steps
                for stuck in remaining:
                    outcome = StepOutcome(
                        step_name=stuck.name,
                        success=False,
                        error="Blocked: dependencies failed or circular dependency detected",
                    )
                    state.record(outcome)
                    if self.on_step_done:
                        self.on_step_done(outcome)
                break

            for step in ready:
                remaining.remove(step)
                step_index += 1
                if self.on_step_start:
                    self.on_step_start(step.name, step_index, total)
                outcome = self._execute_step(step, state)
                state.record(outcome)
                if self.on_step_done:
                    self.on_step_done(outcome)

        return state

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find_ready(
        self, steps: List["Step"], state: ExecutionState
    ) -> List["Step"]:
        """Return steps whose all dependencies are already completed."""
        ready = []
        for step in steps:
            if all(dep in state.completed for dep in step.depends_on):
                # Also check that no dep failed
                if any(dep in state.failed for dep in step.depends_on):
                    continue
                ready.append(step)
        return ready

    def _execute_step(self, step: "Step", state: ExecutionState) -> StepOutcome:
        """Select a tool and run one step, returning an outcome."""
        task = step.to_task_dict()
        tool = self._select_tool(task)

        if tool is None:
            return StepOutcome(
                step_name=step.name,
                success=False,
                error=f"No tool available for capability '{step.capability}' / type '{step.tool_type}'",
            )

        logger.debug(
            "Executing step '%s' with tool '%s'", step.name, getattr(tool, "name", type(tool).__name__)
        )
        start = time.monotonic()
        try:
            result = tool.execute(task, state.context)
        except Exception as exc:
            logger.exception("Unhandled error in tool.execute for step '%s'", step.name)
            result_type = type(None)
            from modules.orchestrator.tools.base import ToolResult
            result = ToolResult(success=False, error=str(exc))

        duration_ms = (time.monotonic() - start) * 1000

        return StepOutcome(
            step_name=step.name,
            success=result.success,
            output=result.output,
            artifacts=result.artifacts,
            cost=result.cost,
            duration_ms=duration_ms,
            error=result.error,
        )

    def _select_tool(self, task: Dict[str, Any]) -> Optional["Tool"]:
        """Return cheapest capable tool for the given task."""
        capable = [t for t in self._tools if t.can_handle(task)]
        if not capable:
            return None
        return min(capable, key=lambda t: t.estimate_cost(task))
