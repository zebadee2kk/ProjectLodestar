"""Script Tool — executes bash or python scripts as orchestration steps.

Scripts receive context values as environment variables and via stdin.
Stdout is captured as the step output. A non-zero exit code is a failure.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import logging

from modules.orchestrator.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

_SCRIPT_CAPABILITIES = ["script", "shell", "bash", "python_script", "test_runner", "formatter"]


class ScriptTool(Tool):
    """Executes a local script (bash or python) as a workflow step.

    Scripts are always free (cost = 0.0) and run in a subprocess with a
    configurable timeout. Context artifacts are injected as environment
    variables with the prefix ``LODESTAR_``.

    Args:
        script_path: Absolute or relative path to the script file.
        script_type: 'bash' or 'python'. Defaults to 'bash'.
        timeout: Maximum seconds to wait. Defaults to 300.
        name: Human-readable tool name for logging.
    """

    def __init__(
        self,
        script_path: str,
        script_type: str = "bash",
        timeout: int = 300,
        name: str = "script",
    ) -> None:
        self.script_path = Path(script_path)
        self.script_type = script_type
        self.timeout = timeout
        self.name = name

    # ------------------------------------------------------------------
    # Tool interface
    # ------------------------------------------------------------------

    def can_handle(self, task: Dict[str, Any]) -> bool:
        cap = task.get("capability", "")
        tool_type = task.get("tool_type", "")
        return cap in _SCRIPT_CAPABILITIES or tool_type == "script"

    def get_capabilities(self) -> List[str]:
        return list(_SCRIPT_CAPABILITIES)

    def estimate_cost(self, task: Dict[str, Any]) -> float:
        return 0.0  # Scripts are always free

    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Run the script, injecting context as env vars."""
        if not self.script_path.exists():
            return ToolResult(
                success=False,
                error=f"Script not found: {self.script_path}",
            )

        env = self._build_env(context, task)
        cmd = self._build_command(task)

        try:
            proc = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=task.get("working_dir", str(self.script_path.parent)),
            )

            output = proc.stdout.strip()
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    output=output,
                    error=proc.stderr.strip() or f"Script exited with code {proc.returncode}",
                    metadata={"returncode": proc.returncode, "stderr": proc.stderr.strip()},
                )

            output_key = task.get("output", "stdout")
            return ToolResult(
                success=True,
                output=output,
                artifacts={output_key: output},
                metadata={"returncode": 0, "stderr": proc.stderr.strip()},
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"Script timed out after {self.timeout}s",
            )
        except Exception as exc:
            logger.exception("ScriptTool execution error")
            return ToolResult(success=False, error=str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_command(self, task: Dict[str, Any]) -> List[str]:
        """Build the subprocess command list."""
        extra_args = task.get("args", [])
        if self.script_type == "python":
            return ["python3", str(self.script_path)] + extra_args
        return ["bash", str(self.script_path)] + extra_args

    def _build_env(self, context: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, str]:
        """Merge OS env with context artifacts as LODESTAR_* variables."""
        env = os.environ.copy()
        for key, value in context.items():
            env_key = f"LODESTAR_{key.upper()}"
            env[env_key] = str(value) if not isinstance(value, str) else value
        # Also inject explicit inputs from task
        for key, value in task.get("inputs", {}).items():
            env_key = f"LODESTAR_{key.upper()}"
            env[env_key] = str(value)
        return env


class InlineScriptTool(ScriptTool):
    """Runs an inline script string (written to a temp file).

    Useful for playbooks that embed short scripts rather than referencing
    external files.

    Args:
        script_content: The script source code.
        script_type: 'bash' or 'python'.
        timeout: Maximum seconds. Defaults to 300.
        name: Tool name for logging.
    """

    def __init__(
        self,
        script_content: str,
        script_type: str = "bash",
        timeout: int = 300,
        name: str = "inline_script",
    ) -> None:
        # Write to a temp file; we'll clean up on __del__
        suffix = ".sh" if script_type == "bash" else ".py"
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False
        )
        self._tmp.write(script_content)
        self._tmp.flush()
        os.chmod(self._tmp.name, 0o755)
        self._tmp.close()
        super().__init__(
            script_path=self._tmp.name,
            script_type=script_type,
            timeout=timeout,
            name=name,
        )

    def __del__(self) -> None:
        try:
            Path(self._tmp.name).unlink(missing_ok=True)
        except Exception:
            pass
