"""Tests for the heuristic diff annotator."""

from modules.diff.annotator import DiffAnnotator


class TestDiffAnnotator:

    def setup_method(self):
        self.annotator = DiffAnnotator()

    def test_function_definition_added(self):
        lines = ["+def new_function():"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Function definition" in text
        assert conf == 0.9

    def test_class_definition_added(self):
        lines = ["+class MyClass:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Class definition" in text

    def test_import_modified(self):
        lines = ["+import os"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Import" in text
        assert conf == 0.95

    def test_removed_function(self):
        lines = ["-def old_function():"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "removed" in text.lower()

    def test_pure_additions(self):
        lines = ["+x = 1", "+y = 2"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Added 2 line(s)" in text

    def test_pure_removals(self):
        lines = ["-x = 1", "-y = 2", "-z = 3"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Removed 3 line(s)" in text

    def test_mixed_changes(self):
        lines = ["-old = 1", "+new = 2"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Modified" in text

    def test_no_changes(self):
        lines = [" unchanged line"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "No changes" in text
        assert conf == 1.0

    def test_empty_lines(self):
        text, conf = self.annotator.annotate_lines([])
        assert "No changes" in text

    def test_return_value_changed(self):
        lines = ["+    return 42"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Return value" in text
        assert conf == 0.8

    def test_raise_exception_modified(self):
        lines = ["+    raise ValueError('bad input')"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Exception handling" in text
        assert conf == 0.85

    def test_conditional_logic(self):
        lines = ["+    if x > 10:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Conditional logic" in text
        assert conf == 0.7

    def test_loop_logic(self):
        lines = ["+    for item in items:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Loop logic" in text

    def test_error_handling(self):
        lines = ["+    try:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Error handling" in text
        assert conf == 0.8

    def test_removed_import(self):
        lines = ["-import deprecated_module"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Import" in text
        assert "removed" in text.lower()
        assert conf == 0.95

    def test_removed_class(self):
        lines = ["-class OldClass:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Class definition" in text
        assert "removed" in text.lower()

    def test_added_lines_checked_before_removed(self):
        """When both added and removed have patterns, added should win."""
        lines = ["+def new_fn():", "-class OldClass:"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Function definition" in text  # added pattern wins

    def test_confidence_varies_by_pattern(self):
        """Different patterns should have different confidence scores."""
        import_text, import_conf = self.annotator.annotate_lines(["+import os"])
        func_text, func_conf = self.annotator.annotate_lines(["+def foo():"])
        cond_text, cond_conf = self.annotator.annotate_lines(["+if True:"])
        assert import_conf > func_conf > cond_conf

    def test_indented_patterns_matched(self):
        """Patterns should match even with leading whitespace."""
        lines = ["+    def indented_function():"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Function definition" in text

    def test_many_plain_additions(self):
        lines = [f"+line_{i} = {i}" for i in range(20)]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Added 20 line(s)" in text
        assert conf == 0.6

    def test_many_plain_removals(self):
        lines = [f"-line_{i}" for i in range(15)]
        text, conf = self.annotator.annotate_lines(lines)
        assert "Removed 15 line(s)" in text

    def test_context_lines_ignored(self):
        """Lines starting with space (context) should not affect detection."""
        lines = [" context line", " another context"]
        text, conf = self.annotator.annotate_lines(lines)
        assert "No changes" in text
