"""Lodestar Agent Framework — Orchestrator Engine.

The OrchestratorEngine is the top-level entry point for multi-step
agent workflows.  It wires together:

  TaskDecomposer  → finds / loads playbooks and converts them to Steps
  StepExecutor    → runs Steps in dependency order using registered Tools
  ResultSynthesizer → stitches outcomes into a final SynthesisResult
  OrchestrationStateStore → persists run history to SQLite

The engine is exposed as a LodestarPlugin so it integrates cleanly with
the existing module lifecycle (start / stop / health_check).

Quick-start::

    from modules.routing.proxy import LodestarProxy
    from modules.orchestrator import OrchestratorEngine

    proxy = LodestarProxy()
    proxy.start()

    engine = OrchestratorEngine({"enabled": True}, proxy=proxy)
    engine.start()

    result = engine.run("Build a REST API for user management")
    print(result.summary)
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from modules.base import LodestarPlugin
from modules.orchestrator.decomposer import TaskDecomposer, Playbook
from modules.orchestrator.executor import StepExecutor, ExecutionState
from modules.orchestrator.synthesizer import ResultSynthesizer, SynthesisResult
from modules.orchestrator.state import OrchestrationStateStore
from modules.orchestrator.tools.llm_tool import LLMTool
from modules.orchestrator.tools.script_tool import ScriptTool, InlineScriptTool
from modules.orchestrator.tools.file_tool import FileTool

logger = logging.getLogger(__name__)


class OrchestratorEngine(LodestarPlugin):
    """Multi-step agent workflow engine.

    Registers LLM, Script, and File tools by default.  Additional tools
    can be added with ``register_tool``.

    Args:
        config: Module config dict.  Recognised keys:

            - ``enabled`` (bool): Whether this module is active.
            - ``playbooks_dir`` (str): Override playbook directory.
            - ``db_path`` (str): Override state database path.
            - ``output_dir`` (str): Base directory for file tool writes.

        proxy: LodestarProxy instance (required for LLM tool).
        event_bus: Optional shared EventBus.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        proxy: Any = None,
        event_bus: Any = None,
    ) -> None:
        super().__init__(config)
        self.proxy = proxy
        self.event_bus = event_bus

        playbooks_dir = config.get("playbooks_dir", "")
        db_path = config.get("db_path", None)
        output_dir = config.get("output_dir", ".")

        self.decomposer = TaskDecomposer(playbooks_dir=playbooks_dir)
        self.state_store = OrchestrationStateStore(db_path=db_path)
        self._output_dir = output_dir

        # Build the tool registry
        self._executor = StepExecutor(
            on_step_start=self._on_step_start,
            on_step_done=self._on_step_done,
        )
        self._synthesis_tool: Optional[LLMTool] = None
        self._current_run_id: Optional[str] = None
        self._progress_callback: Any = None

    # ------------------------------------------------------------------
    # LodestarPlugin interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Register default tools."""
        if self.proxy is not None:
            llm = LLMTool(self.proxy, name="llm_default")
            self._executor.register_tool(llm)
            self._synthesis_tool = LLMTool(
                self.proxy, model_hint="claude-sonnet", name="llm_synthesis"
            )
        file_tool = FileTool(base_dir=self._output_dir, name="file")
        self._executor.register_tool(file_tool)
        logger.info("OrchestratorEngine started (proxy=%s)", self.proxy is not None)

    def stop(self) -> None:
        logger.info("OrchestratorEngine stopped")

    def health_check(self) -> Dict[str, Any]:
        available_playbooks = self.decomposer.list_playbooks()
        return {
            "status": "healthy" if self.enabled else "down",
            "enabled": self.enabled,
            "playbooks_available": len(available_playbooks),
            "playbook_names": available_playbooks,
            "tools_registered": len(self._executor._tools),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_tool(self, tool: Any) -> None:
        """Register an additional tool with the executor."""
        self._executor.register_tool(tool)

    def run(
        self,
        request: str,
        playbook_name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        progress_callback: Any = None,
    ) -> SynthesisResult:
        """Execute a multi-step workflow for the given request.

        Args:
            request: Free-text user request (e.g. "Build a REST API…").
            playbook_name: Force a specific playbook by name.  If None,
                           the decomposer auto-selects based on the request.
            variables: Extra template variables injected into step prompts.
            progress_callback: Optional callable(step_name, index, total)
                               for progress reporting.

        Returns:
            SynthesisResult with artifacts, cost, and summary.
        """
        run_id = str(uuid.uuid4())[:8]
        self._current_run_id = run_id
        self._progress_callback = progress_callback

        # Resolve playbook
        if playbook_name:
            playbook = self.decomposer.load_playbook(playbook_name)
        else:
            playbook = self.decomposer.find_playbook(request)

        resolved_playbook_name = playbook.name if playbook else None
        self.state_store.create_run(run_id, request, playbook=resolved_playbook_name)

        logger.info(
            "Run %s: playbook=%s request='%s'",
            run_id,
            resolved_playbook_name or "(fallback)",
            request[:80],
        )

        # Decompose
        steps = self.decomposer.decompose(
            playbook, user_requirements=request, variables=variables
        )

        # Execute
        state: ExecutionState = self._executor.execute_all(steps)

        # Synthesize
        synthesis_step = None
        if playbook is not None:
            synthesis_step = self.decomposer.build_synthesis_step(playbook, request)
        synthesizer = ResultSynthesizer(tool=self._synthesis_tool)
        result = synthesizer.synthesize(state, synthesis_step=synthesis_step)

        # Persist
        self.state_store.complete_run(
            run_id=run_id,
            success=result.success,
            total_cost=result.total_cost,
            step_count=result.step_count,
            artifacts=result.artifacts,
            summary=result.summary,
        )

        # Publish event
        if self.event_bus is not None:
            self.event_bus.publish(
                "orchestration_completed",
                {
                    "run_id": run_id,
                    "success": result.success,
                    "cost": result.total_cost,
                    "playbook": resolved_playbook_name,
                },
            )

        return result

    def list_playbooks(self) -> List[str]:
        """Return names of all available playbooks."""
        return self.decomposer.list_playbooks()

    def history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent orchestration run summaries."""
        runs = self.state_store.list_runs(limit=limit)
        return [
            {
                "run_id": r.run_id,
                "playbook": r.playbook,
                "request": r.request[:60] + "…" if len(r.request) > 60 else r.request,
                "status": r.status,
                "cost": r.total_cost,
                "steps": r.step_count,
                "started_at": r.started_at,
            }
            for r in runs
        ]

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _on_step_start(self, step_name: str, index: int, total: int) -> None:
        if self._progress_callback:
            self._progress_callback(step_name, index, total)

    def _on_step_done(self, outcome: Any) -> None:
        status = "✓" if outcome.success else "✗"
        cost_str = f"${outcome.cost:.4f}" if outcome.cost > 0 else "FREE"
        logger.debug(
            "%s step '%s' (%.0fms, %s)",
            status,
            outcome.step_name,
            outcome.duration_ms,
            cost_str,
        )
