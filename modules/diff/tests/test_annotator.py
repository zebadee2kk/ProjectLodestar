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
