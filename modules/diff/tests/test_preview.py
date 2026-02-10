"""Tests for the DiffPreview module."""

import pytest
from io import StringIO
from rich.console import Console
from modules.diff.preview import DiffPreview, DiffBlock


SAMPLE_DIFF = """\
diff --git a/hello.py b/hello.py
index abc1234..def5678 100644
--- a/hello.py
+++ b/hello.py
@@ -1,3 +1,4 @@
 import sys
+import os

 def main():
@@ -10,3 +11,5 @@
-    print("hello")
+    print("hello world")
+    return 0
"""


@pytest.fixture
def preview():
    p = DiffPreview({"enabled": True})
    p.start()
    return p


def capture_render(preview_obj, blocks):
    """Helper to capture Rich render output as a string."""
    buf = StringIO()
    preview_obj.console = Console(file=buf, force_terminal=True, width=120)
    preview_obj.render(blocks)
    return buf.getvalue()


class TestDiffPreviewLifecycle:

    def test_start_enabled(self):
        p = DiffPreview({"enabled": True})
        p.start()
        assert p._started is True

    def test_start_disabled(self):
        p = DiffPreview({"enabled": False})
        p.start()
        assert p._started is False

    def test_health_check_started(self, preview):
        health = preview.health_check()
        assert health["status"] == "healthy"

    def test_health_check_stopped(self):
        p = DiffPreview({"enabled": True})
        assert p.health_check()["status"] == "down"


class TestParsing:

    def test_parse_produces_blocks(self, preview):
        blocks = preview.parse_unified_diff(SAMPLE_DIFF)
        assert len(blocks) == 2

    def test_first_block_file_path(self, preview):
        blocks = preview.parse_unified_diff(SAMPLE_DIFF)
        assert blocks[0].file_path == "hello.py"

    def test_first_block_lines(self, preview):
        blocks = preview.parse_unified_diff(SAMPLE_DIFF)
        added_lines = [l for l in blocks[0].lines if l.startswith("+")]
        assert any("import os" in l for l in added_lines)

    def test_second_block_lines(self, preview):
        blocks = preview.parse_unified_diff(SAMPLE_DIFF)
        added = [l for l in blocks[1].lines if l.startswith("+")]
        removed = [l for l in blocks[1].lines if l.startswith("-")]
        assert len(added) == 2
        assert len(removed) == 1

    def test_hunk_header_parsing(self, preview):
        blocks = preview.parse_unified_diff(SAMPLE_DIFF)
        assert blocks[0].old_start == 1
        assert blocks[0].new_start == 1
        assert blocks[1].old_start == 10
        assert blocks[1].new_start == 11

    def test_empty_diff(self, preview):
        blocks = preview.parse_unified_diff("")
        assert blocks == []

    def test_diff_no_hunks(self, preview):
        blocks = preview.parse_unified_diff("just some text\n")
        assert blocks == []


class TestAnnotation:

    def test_annotate_block(self, preview):
        block = DiffBlock(file_path="test.py", old_start=1, new_start=1)
        preview.annotate_block(block, "Added import", 0.9)
        assert block.annotation == "Added import"
        assert block.confidence == 0.9

    def test_annotate_invalid_confidence_high(self, preview):
        block = DiffBlock(file_path="test.py", old_start=1, new_start=1)
        with pytest.raises(ValueError):
            preview.annotate_block(block, "text", 1.5)

    def test_annotate_invalid_confidence_low(self, preview):
        block = DiffBlock(file_path="test.py", old_start=1, new_start=1)
        with pytest.raises(ValueError):
            preview.annotate_block(block, "text", -0.1)

    def test_annotate_boundary_values(self, preview):
        block = DiffBlock(file_path="test.py", old_start=1, new_start=1)
        preview.annotate_block(block, "min", 0.0)
        assert block.confidence == 0.0
        preview.annotate_block(block, "max", 1.0)
        assert block.confidence == 1.0


class TestRendering:
    """Tests for Rich-based render() method."""

    def test_render_shows_file_path(self, preview):
        block = DiffBlock(
            file_path="test.py", old_start=1, new_start=1,
            lines=["+import os"],
        )
        output = capture_render(preview, [block])
        assert "test.py" in output

    def test_render_shows_annotation(self, preview):
        block = DiffBlock(
            file_path="test.py", old_start=1, new_start=1,
            lines=["+import os"],
            annotation="Added os import",
            confidence=0.9,
        )
        output = capture_render(preview, [block])
        assert "Added os import" in output

    def test_render_no_annotation(self, preview):
        block = DiffBlock(
            file_path="test.py", old_start=1, new_start=1,
            lines=["+x = 1"],
        )
        output = capture_render(preview, [block])
        assert "AI:" not in output

    def test_render_empty_lines(self, preview):
        block = DiffBlock(file_path="test.py", old_start=1, new_start=1, lines=[])
        output = capture_render(preview, [block])
        assert "test.py" in output

    def test_render_shows_line_numbers(self, preview):
        block = DiffBlock(file_path="f.py", old_start=42, new_start=50, lines=["+x"])
        output = capture_render(preview, [block])
        assert "42" in output
        assert "50" in output

    def test_render_multiple_blocks(self, preview):
        blocks = [
            DiffBlock(file_path="a.py", old_start=1, new_start=1, lines=["+x"]),
            DiffBlock(file_path="b.py", old_start=5, new_start=5, lines=["-y"]),
        ]
        output = capture_render(preview, blocks)
        assert "a.py" in output
        assert "b.py" in output


class TestMultiFileDiff:
    """Tests for diffs containing multiple files."""

    MULTI_FILE_DIFF = """\
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@
 import sys
+import os
 def foo():
diff --git a/bar.py b/bar.py
--- a/bar.py
+++ b/bar.py
@@ -5,2 +5,3 @@
-    old = 1
+    new = 2
+    extra = 3
"""

    def test_two_files_produce_two_blocks(self, preview):
        blocks = preview.parse_unified_diff(self.MULTI_FILE_DIFF)
        assert len(blocks) == 2

    def test_file_paths_correct(self, preview):
        blocks = preview.parse_unified_diff(self.MULTI_FILE_DIFF)
        assert blocks[0].file_path == "foo.py"
        assert blocks[1].file_path == "bar.py"

    def test_each_block_has_own_lines(self, preview):
        blocks = preview.parse_unified_diff(self.MULTI_FILE_DIFF)
        foo_added = [l for l in blocks[0].lines if l.startswith("+")]
        assert any("import os" in l for l in foo_added)
        bar_added = [l for l in blocks[1].lines if l.startswith("+")]
        assert len(bar_added) == 2


class TestHunkHeaderEdgeCases:
    """Edge cases for _parse_hunk_header."""

    def test_hunk_without_count(self, preview):
        """@@ -5 +7 @@ should parse as old_start=5, new_start=7."""
        old, new = DiffPreview._parse_hunk_header("@@ -5 +7 @@")
        assert old == 5
        assert new == 7

    def test_hunk_with_trailing_context(self, preview):
        """@@ -10,5 +12,7 @@ def some_function()"""
        old, new = DiffPreview._parse_hunk_header(
            "@@ -10,5 +12,7 @@ def some_function()"
        )
        assert old == 10
        assert new == 12

    def test_large_line_numbers(self, preview):
        old, new = DiffPreview._parse_hunk_header("@@ -99999,10 +100005,12 @@")
        assert old == 99999
        assert new == 100005


class TestDiffBlockDataclass:

    def test_defaults(self):
        block = DiffBlock(file_path="f.py", old_start=1, new_start=1)
        assert block.lines == []
        assert block.annotation is None
        assert block.confidence is None

    def test_custom_values(self):
        block = DiffBlock(
            file_path="f.py", old_start=10, new_start=20,
            lines=["+a", "-b"], annotation="test", confidence=0.8
        )
        assert len(block.lines) == 2
        assert block.annotation == "test"
