"""Tests for orchestrator tool implementations."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.orchestrator.tools.base import Tool, ToolResult
from modules.orchestrator.tools.file_tool import FileTool
from modules.orchestrator.tools.llm_tool import LLMTool
from modules.orchestrator.tools.script_tool import InlineScriptTool, ScriptTool


# ---------------------------------------------------------------------------
# FileTool
# ---------------------------------------------------------------------------

class TestFileTool:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.tool = FileTool(base_dir=self.tmp, name="test_file")

    def _task(self, **kwargs):
        base = {"tool_type": "file", "capability": "file_write"}
        base.update(kwargs)
        return base

    def test_can_handle_file_type(self):
        assert self.tool.can_handle({"tool_type": "file"})

    def test_can_handle_file_capability(self):
        assert self.tool.can_handle({"capability": "file_write"})

    def test_cannot_handle_llm(self):
        assert not self.tool.can_handle({"tool_type": "llm", "capability": "code_generation"})

    def test_estimate_cost_is_zero(self):
        assert self.tool.estimate_cost({}) == 0.0

    def test_get_capabilities(self):
        caps = self.tool.get_capabilities()
        assert "file_write" in caps
        assert "file_read" in caps

    def test_write_creates_file(self):
        task = self._task(operation="write", path="hello.txt", content="world")
        result = self.tool.execute(task, {})
        assert result.success
        assert Path(self.tmp, "hello.txt").read_text() == "world"
        assert "written_path" in result.artifacts

    def test_write_content_from_context(self):
        task = self._task(operation="write", path="gen.py", content_from="code")
        ctx = {"code": "print('hello')"}
        result = self.tool.execute(task, ctx)
        assert result.success
        assert "print('hello')" in Path(self.tmp, "gen.py").read_text()

    def test_read_existing_file(self):
        p = Path(self.tmp, "read_me.txt")
        p.write_text("contents here")
        task = self._task(operation="read", path=str(p))
        result = self.tool.execute(task, {})
        assert result.success
        assert result.output == "contents here"
        assert result.artifacts.get("file_content") == "contents here"

    def test_read_missing_file_fails(self):
        task = self._task(operation="read", path="/nonexistent/path.txt")
        result = self.tool.execute(task, {})
        assert not result.success
        assert result.error is not None

    def test_copy_file(self):
        src = Path(self.tmp, "src.txt")
        src.write_text("copy me")
        dst = Path(self.tmp, "dst.txt")
        task = self._task(operation="copy", src=str(src), dst=str(dst))
        result = self.tool.execute(task, {})
        assert result.success
        assert dst.read_text() == "copy me"

    def test_delete_file(self):
        p = Path(self.tmp, "del.txt")
        p.write_text("bye")
        task = self._task(operation="delete", path=str(p))
        result = self.tool.execute(task, {})
        assert result.success
        assert not p.exists()

    def test_unknown_operation_fails(self):
        task = self._task(operation="teleport", path="x.txt")
        result = self.tool.execute(task, {})
        assert not result.success

    def test_write_creates_nested_dirs(self):
        task = self._task(operation="write", path="a/b/c.txt", content="nested")
        result = self.tool.execute(task, {})
        assert result.success
        assert Path(self.tmp, "a", "b", "c.txt").read_text() == "nested"


# ---------------------------------------------------------------------------
# ScriptTool / InlineScriptTool
# ---------------------------------------------------------------------------

class TestScriptTool:
    def test_can_handle_script_type(self):
        tool = ScriptTool("/dev/null")
        assert tool.can_handle({"tool_type": "script"})

    def test_cannot_handle_llm(self):
        tool = ScriptTool("/dev/null")
        assert not tool.can_handle({"tool_type": "llm"})

    def test_estimate_cost_is_zero(self):
        tool = ScriptTool("/dev/null")
        assert tool.estimate_cost({}) == 0.0

    def test_missing_script_fails(self):
        tool = ScriptTool("/no/such/script.sh")
        result = tool.execute({"tool_type": "script"}, {})
        assert not result.success
        assert "not found" in result.error.lower()


class TestInlineScriptTool:
    def test_bash_script_success(self):
        tool = InlineScriptTool("echo 'hello world'", script_type="bash")
        result = tool.execute({"tool_type": "script"}, {})
        assert result.success
        assert "hello world" in result.output

    def test_bash_script_failure(self):
        tool = InlineScriptTool("exit 1", script_type="bash")
        result = tool.execute({"tool_type": "script"}, {})
        assert not result.success

    def test_context_injected_as_env(self):
        tool = InlineScriptTool("echo $LODESTAR_GREETING", script_type="bash")
        result = tool.execute({"tool_type": "script"}, {"greeting": "hello"})
        assert result.success
        assert "hello" in result.output

    def test_python_script_success(self):
        tool = InlineScriptTool("print('from python')", script_type="python")
        result = tool.execute({"tool_type": "script"}, {})
        assert result.success
        assert "from python" in result.output

    def test_timeout_respected(self):
        tool = InlineScriptTool("sleep 10", script_type="bash", timeout=1)
        result = tool.execute({"tool_type": "script"}, {})
        assert not result.success
        assert "timed out" in result.error.lower()

    def test_output_key_in_artifacts(self):
        tool = InlineScriptTool("echo 'value'", script_type="bash")
        task = {"tool_type": "script", "output": "my_key"}
        result = tool.execute(task, {})
        assert result.success
        assert "my_key" in result.artifacts


# ---------------------------------------------------------------------------
# LLMTool
# ---------------------------------------------------------------------------

class TestLLMTool:
    def _make_proxy(self, response_text="LLM response"):
        proxy = MagicMock()
        proxy.handle_request.return_value = {
            "task": "general",
            "model": "gpt-3.5-turbo",
            "result": MagicMock(success=True, response=response_text),
            "cost_entry": {"cost": 0.0, "savings": 0.0},
        }
        return proxy

    def test_can_handle_llm_type(self):
        tool = LLMTool(MagicMock())
        assert tool.can_handle({"tool_type": "llm"})

    def test_can_handle_code_generation(self):
        tool = LLMTool(MagicMock())
        assert tool.can_handle({"capability": "code_generation"})

    def test_cannot_handle_script(self):
        tool = LLMTool(MagicMock())
        assert not tool.can_handle({"tool_type": "script", "capability": "shell"})

    def test_get_capabilities_includes_planning(self):
        tool = LLMTool(MagicMock())
        assert "planning" in tool.get_capabilities()

    def test_execute_returns_tool_result(self):
        proxy = self._make_proxy("def hello(): pass")
        tool = LLMTool(proxy)
        task = {"tool_type": "llm", "capability": "code_generation", "prompt": "Write hello func", "output": "code"}
        result = tool.execute(task, {})
        assert result.success
        assert result.output == "def hello(): pass"
        assert result.artifacts.get("code") == "def hello(): pass"

    def test_execute_substitutes_context_in_prompt(self):
        proxy = self._make_proxy("ok")
        tool = LLMTool(proxy)
        task = {"tool_type": "llm", "capability": "general", "prompt": "Use {schema} here", "output": "result"}
        result = tool.execute(task, {"schema": "CREATE TABLE x (id INT);"})
        assert result.success
        # Verify the prompt sent to proxy was substituted
        call_kwargs = proxy.handle_request.call_args
        assert "CREATE TABLE x" in call_kwargs[1]["prompt"] or "CREATE TABLE x" in call_kwargs[0][0]

    def test_execute_handles_proxy_failure(self):
        proxy = MagicMock()
        proxy.handle_request.side_effect = RuntimeError("Connection refused")
        tool = LLMTool(proxy)
        task = {"tool_type": "llm", "capability": "general", "prompt": "test"}
        result = tool.execute(task, {})
        assert not result.success
        assert result.error is not None

    def test_estimate_cost_free_model(self):
        tool = LLMTool(MagicMock(), model_hint="gpt-3.5-turbo")
        assert tool.estimate_cost({"prompt": "hello"}) == 0.0

    def test_estimate_cost_paid_model(self):
        tool = LLMTool(MagicMock(), model_hint="claude-sonnet")
        cost = tool.estimate_cost({"prompt": "hello world"})
        assert cost > 0.0
