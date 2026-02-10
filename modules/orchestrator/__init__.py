"""Lodestar Agent Framework — Orchestrator module.

The orchestrator turns Lodestar from a routing layer into a full
multi-step agent platform.  It chains LLM calls, scripts, and file
operations into reproducible YAML-driven workflows.

Public API::

    from modules.orchestrator import OrchestratorEngine

    engine = OrchestratorEngine({"enabled": True}, proxy=proxy)
    engine.start()
    result = engine.run("Build a REST API with PostgreSQL")
    print(result.summary)
"""

from modules.orchestrator.core import OrchestratorEngine
from modules.orchestrator.decomposer import TaskDecomposer, Playbook, Step
from modules.orchestrator.executor import StepExecutor, ExecutionState, StepOutcome
from modules.orchestrator.synthesizer import ResultSynthesizer, SynthesisResult
from modules.orchestrator.tools import Tool, ToolResult, LLMTool, ScriptTool, FileTool

__all__ = [
    "OrchestratorEngine",
    "TaskDecomposer",
    "Playbook",
    "Step",
    "StepExecutor",
    "ExecutionState",
    "StepOutcome",
    "ResultSynthesizer",
    "SynthesisResult",
    "Tool",
    "ToolResult",
    "LLMTool",
    "ScriptTool",
    "FileTool",
]
