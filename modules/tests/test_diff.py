import pytest
from unittest.mock import MagicMock, patch
from modules.diff.annotator import DiffAnnotator
from modules.diff.preview import DiffPreview, DiffBlock
from modules.routing.proxy import LodestarProxy

class TestDiffAnnotator:
    @pytest.fixture
    def mock_proxy(self):
        proxy = MagicMock(spec=LodestarProxy)
        return proxy

    def test_annotate_no_changes(self, mock_proxy):
        annotator = DiffAnnotator(mock_proxy)
        annotation, conf = annotator.annotate("test.py", [])
        assert annotation == "No changes detected"
        assert conf == 1.0

    def test_annotate_fallback(self, mock_proxy):
        # Setup mock to fail
        mock_proxy.handle_request.side_effect = Exception("LLM Error")
        
        annotator = DiffAnnotator(mock_proxy)
        diff_lines = ["+ def new_func():", "+     pass"]
        annotation, conf = annotator.annotate("test.py", diff_lines)
        
        assert "Added 2 line(s)" in annotation
        assert conf == 0.5

    def test_annotate_llm_success(self, mock_proxy):
        # Setup mock success
        mock_result = MagicMock()
        mock_result.result.success = True
        mock_result.result.response = "Added a new function."
        mock_proxy.handle_request.return_value = {"result": mock_result.result}

        annotator = DiffAnnotator(mock_proxy)
        diff_lines = ["+ def new_func():", "+     pass"]
        annotation, conf = annotator.annotate("test.py", diff_lines)

        assert annotation == "Added a new function."
        assert conf == 0.9

class TestDiffPreview:
    def test_parse_unified_diff(self):
        diff_text = """diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 line1
+line2
 line3"""
        
        preview = DiffPreview({"enabled": True})
        blocks = preview.parse_unified_diff(diff_text)
        
        assert len(blocks) == 1
        assert blocks[0].file_path == "test.py"
        assert blocks[0].old_start == 1
        assert blocks[0].new_start == 1
        assert len(blocks[0].lines) == 3
        assert blocks[0].lines[1] == "+line2"
