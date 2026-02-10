"""File Tool — reads, writes, and manages files as orchestration steps.

Artifacts from prior steps can be written to disk; files can be read
back into context. All operations are local and free.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List
import logging

from modules.orchestrator.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

_FILE_CAPABILITIES = ["file_write", "file_read", "file_copy", "file_delete", "file_list"]


class FileTool(Tool):
    """Reads and writes files on the local filesystem.

    Supports four operations controlled by ``task['operation']``:
    - ``write``: Write ``task['content']`` (or context artifact) to ``task['path']``.
    - ``read``: Read file at ``task['path']`` into context.
    - ``copy``: Copy ``task['src']`` to ``task['dst']``.
    - ``delete``: Delete file at ``task['path']``.

    All operations are free (cost = 0.0).

    Args:
        base_dir: Optional base directory. Relative paths are resolved from here.
        name: Human-readable tool name for logging.
    """

    def __init__(self, base_dir: str = ".", name: str = "file") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.name = name

    # ------------------------------------------------------------------
    # Tool interface
    # ------------------------------------------------------------------

    def can_handle(self, task: Dict[str, Any]) -> bool:
        cap = task.get("capability", "")
        tool_type = task.get("tool_type", "")
        return cap in _FILE_CAPABILITIES or tool_type == "file"

    def get_capabilities(self) -> List[str]:
        return list(_FILE_CAPABILITIES)

    def estimate_cost(self, task: Dict[str, Any]) -> float:
        return 0.0

    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        operation = task.get("operation", "write")
        dispatch = {
            "write": self._write,
            "read": self._read,
            "copy": self._copy,
            "delete": self._delete,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return ToolResult(success=False, error=f"Unknown file operation: '{operation}'")
        return handler(task, context)

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _write(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        path = self._resolve(task.get("path", ""))
        if not path:
            return ToolResult(success=False, error="'path' is required for file_write")

        # Content can be explicit or pulled from a context artifact
        content = task.get("content")
        if content is None:
            artifact_key = task.get("content_from")
            if artifact_key:
                content = context.get(artifact_key, "")
            else:
                content = ""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        logger.debug("FileTool wrote %d bytes to %s", len(str(content)), path)

        output_key = task.get("output", "written_path")
        return ToolResult(
            success=True,
            output=str(path),
            artifacts={output_key: str(path)},
            metadata={"bytes_written": len(str(content))},
        )

    def _read(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        path = self._resolve(task.get("path", ""))
        if not path or not path.exists():
            return ToolResult(success=False, error=f"File not found: {task.get('path')}")

        content = path.read_text(encoding="utf-8")
        output_key = task.get("output", "file_content")
        return ToolResult(
            success=True,
            output=content,
            artifacts={output_key: content},
            metadata={"path": str(path), "bytes": len(content)},
        )

    def _copy(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        src = self._resolve(task.get("src", ""))
        dst = self._resolve(task.get("dst", ""))
        if not src or not src.exists():
            return ToolResult(success=False, error=f"Source not found: {task.get('src')}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        output_key = task.get("output", "copied_path")
        return ToolResult(
            success=True,
            output=str(dst),
            artifacts={output_key: str(dst)},
        )

    def _delete(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        path = self._resolve(task.get("path", ""))
        if not path or not path.exists():
            return ToolResult(success=False, error=f"File not found: {task.get('path')}")
        path.unlink()
        return ToolResult(success=True, output=str(path))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, rel_path: str) -> Path:
        if not rel_path:
            return Path("")
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return (self.base_dir / p).resolve()
