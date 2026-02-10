"""Task Decomposer — breaks a user request into an ordered list of steps.

The decomposer inspects a playbook (YAML workflow definition) and
resolves it into a flat list of Step objects with dependency edges.
If no playbook matches, it falls back to a single-step LLM execution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """A single unit of work within an orchestration run.

    Attributes:
        name: Unique identifier within this run.
        tool_type: 'llm', 'script', or 'file'.
        capability: Semantic capability tag (e.g. 'code_generation').
        prompt: Optional prompt template (LLM steps).
        script_path: Path to script file (script steps).
        script_type: 'bash' or 'python'.
        operation: File operation type (file steps).
        path: File path (file steps).
        content: Static content (file write steps).
        content_from: Context key to pull content from.
        inputs: Explicit key→value inputs injected into context.
        depends_on: Names of steps that must complete before this one.
        output: Key name under which to store this step's output.
        preferred_model: Optional LLM model override.
        max_tokens: Token limit for LLM steps.
        args: Extra CLI args for script steps.
        working_dir: Working directory for script steps.
        metadata: Any extra playbook fields.
    """

    name: str
    tool_type: str = "llm"
    capability: str = "general"
    prompt: str = ""
    script_path: str = ""
    script_type: str = "bash"
    operation: str = "write"
    path: str = ""
    content: Optional[str] = None
    content_from: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    output: str = ""
    preferred_model: Optional[str] = None
    max_tokens: int = 4096
    args: List[str] = field(default_factory=list)
    working_dir: str = "."
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_task_dict(self) -> Dict[str, Any]:
        """Convert to the task dict format consumed by tools."""
        return {
            "name": self.name,
            "tool_type": self.tool_type,
            "capability": self.capability,
            "prompt": self.prompt,
            "script_path": self.script_path,
            "script_type": self.script_type,
            "operation": self.operation,
            "path": self.path,
            "content": self.content,
            "content_from": self.content_from,
            "inputs": self.inputs,
            "output": self.output or self.name,
            "preferred_model": self.preferred_model,
            "max_tokens": self.max_tokens,
            "args": self.args,
            "working_dir": self.working_dir,
            **self.metadata,
        }


@dataclass
class Playbook:
    """A parsed workflow definition loaded from YAML.

    Attributes:
        name: Playbook identifier.
        description: Human-readable description.
        steps: Ordered list of Step objects.
        synthesis: Optional synthesis step config dict.
        metadata: Any top-level playbook fields.
    """

    name: str
    description: str = ""
    steps: List[Step] = field(default_factory=list)
    synthesis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskDecomposer:
    """Loads playbooks and decomposes user requests into step sequences.

    Usage::

        decomposer = TaskDecomposer(playbooks_dir="modules/orchestrator/playbooks")
        playbook = decomposer.find_playbook("rest api")
        steps = decomposer.decompose(playbook, user_requirements="Build user mgmt")

    Args:
        playbooks_dir: Directory containing ``*.yaml`` playbook files.
    """

    def __init__(self, playbooks_dir: str = "") -> None:
        if not playbooks_dir:
            playbooks_dir = str(Path(__file__).parent / "playbooks")
        self.playbooks_dir = Path(playbooks_dir)
        self._cache: Dict[str, Playbook] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_playbooks(self) -> List[str]:
        """Return names of all available playbooks."""
        return [p.stem for p in sorted(self.playbooks_dir.glob("*.yaml"))]

    def load_playbook(self, name: str) -> Optional[Playbook]:
        """Load a playbook by name (filename without .yaml).

        Returns None if the playbook file does not exist.
        """
        if name in self._cache:
            return self._cache[name]

        path = self.playbooks_dir / f"{name}.yaml"
        if not path.exists():
            logger.warning("Playbook not found: %s", path)
            return None

        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}

        playbook = self._parse_playbook(name, raw)
        self._cache[name] = playbook
        return playbook

    def find_playbook(self, query: str) -> Optional[Playbook]:
        """Find the best matching playbook for a free-text query.

        Scores each playbook by keyword overlap with the query and
        returns the highest scoring one, or None if all score 0.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        best_name: Optional[str] = None
        best_score = 0

        for name in self.list_playbooks():
            playbook = self.load_playbook(name)
            if playbook is None:
                continue
            description_words = set(re.findall(r"\w+", playbook.description.lower()))
            name_words = set(re.findall(r"\w+", name.lower()))
            candidate_words = description_words | name_words
            score = len(query_words & candidate_words)
            if score > best_score:
                best_score = score
                best_name = name

        if best_name and best_score > 0:
            return self.load_playbook(best_name)
        return None

    def decompose(
        self,
        playbook: Optional[Playbook],
        user_requirements: str = "",
        variables: Optional[Dict[str, Any]] = None,
    ) -> List[Step]:
        """Return ordered steps for execution.

        If no playbook is given, falls back to a single general LLM step.
        Injects ``user_requirements`` and ``variables`` into prompt templates.

        Args:
            playbook: Loaded Playbook or None for fallback.
            user_requirements: Free-text description from the user.
            variables: Extra template variables to substitute.
        """
        if playbook is None:
            return self._fallback_steps(user_requirements)

        context = {"user_requirements": user_requirements}
        if variables:
            context.update(variables)

        steps = []
        for step in playbook.steps:
            substituted = self._substitute_step(step, context)
            steps.append(substituted)

        return steps

    def build_synthesis_step(
        self, playbook: Playbook, user_requirements: str = ""
    ) -> Optional[Step]:
        """Build the optional synthesis step from a playbook definition."""
        if not playbook.synthesis:
            return None
        raw = dict(playbook.synthesis)
        raw.setdefault("name", "_synthesis")
        raw.setdefault("tool_type", "llm")
        raw.setdefault("capability", "synthesis")
        context = {"user_requirements": user_requirements}
        step = self._parse_step(raw)
        return self._substitute_step(step, context)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_playbook(self, name: str, raw: Dict[str, Any]) -> Playbook:
        steps_raw = raw.pop("steps", [])
        synthesis = raw.pop("synthesis", None)
        pb = Playbook(
            name=raw.pop("name", name),
            description=raw.pop("description", ""),
            synthesis=synthesis,
            metadata=raw,
        )
        for s in steps_raw:
            pb.steps.append(self._parse_step(s))
        return pb

    def _parse_step(self, raw: Dict[str, Any]) -> Step:
        known_keys = {
            "name", "tool_type", "capability", "prompt", "script_path",
            "script_type", "operation", "path", "content", "content_from",
            "inputs", "depends_on", "output", "preferred_model", "max_tokens",
            "args", "working_dir",
        }
        metadata = {k: v for k, v in raw.items() if k not in known_keys}
        return Step(
            name=raw.get("name", "unnamed"),
            tool_type=raw.get("tool_type", "llm"),
            capability=raw.get("capability", "general"),
            prompt=raw.get("prompt", ""),
            script_path=raw.get("script_path", ""),
            script_type=raw.get("script_type", "bash"),
            operation=raw.get("operation", "write"),
            path=raw.get("path", ""),
            content=raw.get("content"),
            content_from=raw.get("content_from"),
            inputs=raw.get("inputs", {}),
            depends_on=raw.get("depends_on", []),
            output=raw.get("output", raw.get("name", "result")),
            preferred_model=raw.get("preferred_model"),
            max_tokens=raw.get("max_tokens", 4096),
            args=raw.get("args", []),
            working_dir=raw.get("working_dir", "."),
            metadata=metadata,
        )

    def _substitute_step(self, step: Step, context: Dict[str, Any]) -> Step:
        """Return a copy of ``step`` with {variable} placeholders substituted."""
        import copy
        s = copy.deepcopy(step)
        s.prompt = self._sub(s.prompt, context)
        s.path = self._sub(s.path, context)
        if s.content is not None:
            s.content = self._sub(s.content, context)
        return s

    @staticmethod
    def _sub(text: str, context: Dict[str, Any]) -> str:
        for key, val in context.items():
            text = text.replace("{" + key + "}", str(val))
        return text

    def _fallback_steps(self, user_requirements: str) -> List[Step]:
        """Single-step fallback when no playbook matches."""
        return [
            Step(
                name="execute",
                tool_type="llm",
                capability="general",
                prompt=user_requirements or "Please help with the following task.",
                output="result",
            )
        ]
