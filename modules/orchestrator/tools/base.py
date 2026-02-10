"""Base tool interface for the Lodestar Orchestrator.

All tool implementations must subclass Tool and implement:
- can_handle(task) — capability check
- execute(task, context) — task execution
- get_capabilities() — list of supported capability tags
- estimate_cost(task) — estimated cost in USD (0.0 = free)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Result from a tool execution.

    Attributes:
        success: Whether execution succeeded.
        output: The primary output data (file path, text, etc.).
        artifacts: Named outputs that downstream steps can reference.
        error: Error message if success is False.
        cost: Actual cost incurred (USD).
        metadata: Tool-specific extra data.
    """

    success: bool
    output: Any = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Abstract base class for all Orchestrator tools.

    A tool represents a capability that can be invoked during workflow
    execution. Tools are self-describing: they declare what they can
    handle and estimate cost before execution is committed.
    """

    @abstractmethod
    def can_handle(self, task: Dict[str, Any]) -> bool:
        """Return True if this tool can execute the given task.

        Args:
            task: Task dict containing at minimum a 'capability' key.
        """

    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the task and return a ToolResult.

        Args:
            task: Task specification (capability, inputs, prompt, etc.).
            context: Shared context / outputs from prior steps.
        """

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capability tags this tool supports.

        Examples: ['code_generation', 'documentation', 'llm']
        """

    @abstractmethod
    def estimate_cost(self, task: Dict[str, Any]) -> float:
        """Estimate cost in USD to execute this task.

        Free tools (scripts, local LLMs) should return 0.0.
        """
