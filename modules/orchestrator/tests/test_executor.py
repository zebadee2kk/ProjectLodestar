"""Tests for StepExecutor — dependency resolution and tool dispatch."""

from unittest.mock import MagicMock

import pytest

from modules.orchestrator.decomposer import Step
from modules.orchestrator.executor import ExecutionState, StepExecutor, StepOutcome
from modules.orchestrator.tools.base import Tool, ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_step(name, tool_type="llm", capability="general", depends_on=None):
    return Step(
        name=name,
        tool_type=tool_type,
        capability=capability,
        prompt="test",
        output=name,
        depends_on=depends_on or [],
    )


def _succeed_tool(name="mock_tool"):
    tool = MagicMock(spec=Tool)
    tool.name = name
    tool.can_handle.return_value = True
    tool.estimate_cost.return_value = 0.0
    tool.execute.return_value = ToolResult(
        success=True, output=f"{name}_output", artifacts={name: f"{name}_output"}
    )
    return tool


def _fail_tool(name="fail_tool", error="deliberate failure"):
    tool = MagicMock(spec=Tool)
    tool.name = name
    tool.can_handle.return_value = True
    tool.estimate_cost.return_value = 0.0
    tool.execute.return_value = ToolResult(success=False, error=error)
    return tool


# ---------------------------------------------------------------------------
# ExecutionState
# ---------------------------------------------------------------------------

class TestExecutionState:
    def test_initial_state(self):
        state = ExecutionState()
        assert state.total_cost == 0.0
        assert state.success  # No failures yet

    def test_record_success(self):
        state = ExecutionState()
        outcome = StepOutcome(
            step_name="step1",
            success=True,
            output="result",
            artifacts={"key": "value"},
            cost=0.005,
        )
        state.record(outcome)
        assert "step1" in state.completed
        assert state.context["key"] == "value"
        assert state.total_cost == pytest.approx(0.005)
        assert state.success

    def test_record_failure(self):
        state = ExecutionState()
        outcome = StepOutcome(step_name="bad", success=False, error="oops")
        state.record(outcome)
        assert "bad" in state.failed
        assert not state.success

    def test_summary(self):
        state = ExecutionState()
        state.record(StepOutcome("a", True, cost=0.01))
        state.record(StepOutcome("b", False, error="fail"))
        s = state.summary()
        assert s["steps_completed"] == 1
        assert s["steps_failed"] == 1
        assert not s["success"]


# ---------------------------------------------------------------------------
# StepExecutor — no tools
# ---------------------------------------------------------------------------

class TestStepExecutorNoTools:
    def setup_method(self):
        self.executor = StepExecutor()

    def test_no_tool_produces_failure(self):
        step = _make_step("s1")
        state = self.executor.execute_all([step])
        assert "s1" in state.failed

    def test_error_message_mentions_capability(self):
        step = _make_step("s1", capability="code_generation")
        state = self.executor.execute_all([step])
        outcome = state.outcomes[0]
        assert "code_generation" in outcome.error


# ---------------------------------------------------------------------------
# StepExecutor — single tool, single step
# ---------------------------------------------------------------------------

class TestStepExecutorSingleStep:
    def setup_method(self):
        self.executor = StepExecutor()
        self.tool = _succeed_tool("t1")
        self.executor.register_tool(self.tool)

    def test_success(self):
        step = _make_step("s1")
        state = self.executor.execute_all([step])
        assert "s1" in state.completed
        assert state.success

    def test_output_in_context(self):
        self.tool.execute.return_value = ToolResult(
            success=True, output="hello", artifacts={"s1": "hello"}
        )
        state = self.executor.execute_all([_make_step("s1")])
        assert state.context["s1"] == "hello"

    def test_step_start_callback_called(self):
        calls = []
        executor = StepExecutor(on_step_start=lambda name, i, t: calls.append((name, i, t)))
        executor.register_tool(_succeed_tool())
        executor.execute_all([_make_step("s1")])
        assert len(calls) == 1
        assert calls[0][0] == "s1"

    def test_step_done_callback_called(self):
        outcomes = []
        executor = StepExecutor(on_step_done=lambda o: outcomes.append(o))
        executor.register_tool(_succeed_tool())
        executor.execute_all([_make_step("s1")])
        assert len(outcomes) == 1
        assert outcomes[0].success


# ---------------------------------------------------------------------------
# StepExecutor — dependency ordering
# ---------------------------------------------------------------------------

class TestStepExecutorDependencies:
    def setup_method(self):
        self.executor = StepExecutor()
        self.tool = _succeed_tool()
        self.executor.register_tool(self.tool)

    def test_linear_chain_executes_in_order(self):
        order = []
        executor = StepExecutor(on_step_start=lambda n, i, t: order.append(n))
        executor.register_tool(_succeed_tool())
        steps = [
            _make_step("a"),
            _make_step("b", depends_on=["a"]),
            _make_step("c", depends_on=["b"]),
        ]
        state = executor.execute_all(steps)
        assert order == ["a", "b", "c"]
        assert state.success

    def test_failed_dependency_blocks_child(self):
        fail_exec = StepExecutor()
        fail_exec.register_tool(_fail_tool())
        steps = [
            _make_step("parent"),
            _make_step("child", depends_on=["parent"]),
        ]
        state = fail_exec.execute_all(steps)
        assert "parent" in state.failed
        assert "child" in state.failed

    def test_independent_steps_both_run(self):
        steps = [_make_step("x"), _make_step("y")]
        state = self.executor.execute_all(steps)
        assert "x" in state.completed
        assert "y" in state.completed

    def test_context_flows_between_steps(self):
        executor = StepExecutor()
        # Single tool — captures context on each call
        received_contexts = []
        call_count = [0]

        def capture_execute(task, context):
            received_contexts.append(dict(context))
            call_count[0] += 1
            if call_count[0] == 1:
                return ToolResult(
                    success=True, output="upstream_value",
                    artifacts={"upstream": "upstream_value"}
                )
            return ToolResult(success=True, output="done", artifacts={"done": "done"})

        tool = MagicMock(spec=Tool)
        tool.can_handle.return_value = True
        tool.estimate_cost.return_value = 0.0
        tool.execute.side_effect = capture_execute
        executor.register_tool(tool)

        steps = [
            _make_step("upstream"),
            _make_step("downstream", depends_on=["upstream"]),
        ]
        executor.execute_all(steps)
        # Second call should have received upstream's artifact in context
        assert len(received_contexts) == 2
        assert received_contexts[1].get("upstream") == "upstream_value"

    def test_circular_dependency_does_not_hang(self):
        # Both steps depend on each other — neither should ever become ready
        steps = [
            _make_step("a", depends_on=["b"]),
            _make_step("b", depends_on=["a"]),
        ]
        state = self.executor.execute_all(steps)
        # Both should be recorded as blocked failures
        assert len(state.failed) == 2

    def test_cheapest_tool_selected(self):
        cheap = MagicMock(spec=Tool)
        cheap.can_handle.return_value = True
        cheap.estimate_cost.return_value = 0.0
        cheap.execute.return_value = ToolResult(success=True, output="cheap", artifacts={})

        expensive = MagicMock(spec=Tool)
        expensive.can_handle.return_value = True
        expensive.estimate_cost.return_value = 10.0
        expensive.execute.return_value = ToolResult(success=True, output="expensive", artifacts={})

        executor = StepExecutor()
        executor.register_tool(expensive)
        executor.register_tool(cheap)
        executor.execute_all([_make_step("s")])

        assert cheap.execute.called
        assert not expensive.execute.called
