"""Tests for the DiffPreview module."""

import pytest
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


class TestFormatting:

    def test_format_basic_block(self, preview):
        block = DiffBlock(
            file_path="test.py",
            old_start=1,
            new_start=1,
            lines=["+import os"],
        )
        output = preview.format_block(block)
        assert "test.py" in output
        assert "+import os" in output

    def test_format_with_annotation(self, preview):
        block = DiffBlock(
            file_path="test.py",
            old_start=1,
            new_start=1,
            lines=["+import os"],
            annotation="Added os import",
            confidence=0.9,
        )
        output = preview.format_block(block)
        assert "AI" in output
        assert "90%" in output
        assert "Added os import" in output

    def test_format_without_annotation(self, preview):
        block = DiffBlock(
            file_path="test.py",
            old_start=1,
            new_start=1,
            lines=["+x = 1"],
        )
        output = preview.format_block(block)
        assert "AI" not in output
