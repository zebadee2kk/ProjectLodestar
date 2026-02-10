"""Tests for the LLM-powered diff annotator."""

from unittest.mock import MagicMock, patch
import pytest

from modules.diff.annotator import DiffAnnotator


class MockProxy:
    """Minimal proxy mock for DiffAnnotator tests."""

    def __init__(self, response_text="Refactored for clarity", success=True):
        self._response_text = response_text
        self._success = success

    def handle_request(self, prompt, task_override=None):
        result = MagicMock()
        result.success = self._success
        result.response = self._response_text if self._success else None
        return {"result": result}


class TestAnnotateWithLLM:
    """Tests for the LLM-powered annotate() path."""

    def setup_method(self):
        self.proxy = MockProxy()
        self.annotator = DiffAnnotator(self.proxy)

    def test_annotate_returns_tuple(self):
        text, conf = self.annotator.annotate("test.py", ["+import os"])
        assert isinstance(text, str)
        assert isinstance(conf, float)

    def test_annotate_success_returns_llm_response(self):
        text, conf = self.annotator.annotate("test.py", ["+import os"])
        assert text == "Refactored for clarity"
        assert conf == 0.9

    def test_annotate_empty_lines_returns_no_changes(self):
        text, conf = self.annotator.annotate("test.py", [])
        assert "No changes" in text
        assert conf == 1.0

    def test_annotate_passes_file_path_in_prompt(self):
        proxy = MagicMock()
        result = MagicMock()
        result.success = True
        result.response = "Explanation"
        proxy.handle_request.return_value = {"result": result}

        annotator = DiffAnnotator(proxy)
        annotator.annotate("src/utils.py", ["+x = 1"])

        call_args = proxy.handle_request.call_args
        assert "src/utils.py" in call_args.kwargs.get("prompt", call_args[1].get("prompt", "")) or \
               "src/utils.py" in str(call_args)

    def test_annotate_passes_task_override(self):
        proxy = MagicMock()
        result = MagicMock()
        result.success = True
        result.response = "Explanation"
        proxy.handle_request.return_value = {"result": result}

        annotator = DiffAnnotator(proxy)
        annotator.annotate("test.py", ["+x = 1"])

        call_args = proxy.handle_request.call_args
        assert call_args.kwargs.get("task_override") == "code_explanation"

    def test_annotate_llm_failure_falls_back(self):
        proxy = MockProxy(success=False)
        annotator = DiffAnnotator(proxy)
        text, conf = annotator.annotate("test.py", ["+x = 1"])
        # Fallback heuristic returns 0.5 confidence
        assert conf == 0.5

    def test_annotate_exception_falls_back(self):
        proxy = MagicMock()
        proxy.handle_request.side_effect = RuntimeError("Connection failed")
        annotator = DiffAnnotator(proxy)
        text, conf = annotator.annotate("test.py", ["+x = 1"])
        assert conf == 0.5

    def test_annotate_strips_whitespace(self):
        proxy = MockProxy(response_text="  Trimmed response  ")
        annotator = DiffAnnotator(proxy)
        text, conf = annotator.annotate("test.py", ["+x = 1"])
        assert text == "Trimmed response"


class TestFallbackHeuristic:
    """Tests for the _fallback_heuristic method."""

    def setup_method(self):
        self.proxy = MockProxy()
        self.annotator = DiffAnnotator(self.proxy)

    def test_pure_additions(self):
        text, conf = self.annotator._fallback_heuristic(["+x = 1", "+y = 2"])
        assert "Added 2 line(s)" in text
        assert conf == 0.5

    def test_pure_removals(self):
        text, conf = self.annotator._fallback_heuristic(["-x = 1", "-y = 2", "-z = 3"])
        assert "Removed 3 line(s)" in text
        assert conf == 0.5

    def test_mixed_changes(self):
        text, conf = self.annotator._fallback_heuristic(["-old = 1", "+new = 2"])
        assert "Modified" in text
        assert conf == 0.5

    def test_single_addition(self):
        text, conf = self.annotator._fallback_heuristic(["+import os"])
        assert "Added 1 line(s)" in text

    def test_single_removal(self):
        text, conf = self.annotator._fallback_heuristic(["-import os"])
        assert "Removed 1 line(s)" in text

    def test_many_additions(self):
        lines = [f"+line_{i}" for i in range(20)]
        text, conf = self.annotator._fallback_heuristic(lines)
        assert "Added 20 line(s)" in text

    def test_many_removals(self):
        lines = [f"-line_{i}" for i in range(15)]
        text, conf = self.annotator._fallback_heuristic(lines)
        assert "Removed 15 line(s)" in text

    def test_context_lines_not_counted(self):
        """Context lines (space prefix) should not affect added/removed counts."""
        lines = [" context", "+added"]
        text, conf = self.annotator._fallback_heuristic(lines)
        assert "Added 1 line(s)" in text

    def test_empty_lines_returns_modified(self):
        """Empty list with no +/- lines returns Modified logic."""
        text, conf = self.annotator._fallback_heuristic([])
        assert "Modified" in text
