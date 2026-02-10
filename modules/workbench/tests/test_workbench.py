"""Tests for the Workbench module."""

import pytest
from unittest.mock import MagicMock, patch
from modules.workbench.orchestrator import WorkbenchOrchestrator


class TestWorkbenchOrchestrator:
    @patch("modules.workbench.orchestrator.MemoryModule")
    @patch("modules.workbench.orchestrator.ContextModule")
    @patch("modules.workbench.orchestrator.KnowledgeModule")
    def test_process_request(self, mock_know, mock_ctx, mock_mem):
        # Setup mocks
        mock_mem_inst = mock_mem.return_value
        mock_ctx_inst = mock_ctx.return_value
        mock_know_inst = mock_know.return_value
        mock_proxy_inst = MagicMock()
        
        mock_ctx_inst.create_session.return_value = "s123"
        mock_know_inst.search.return_value = [{"text": "file info", "metadata": {"path": "src/main.py"}}]
        mock_mem_inst.search.return_value = [{"text": "past info"}]
        
        # Mock Proxy handle_request
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="AI Response"))]
        mock_proxy_inst.handle_request.return_value = {
            "model": "gpt-4",
            "task": "coding",
            "result": MagicMock(success=True, response=mock_resp),
            "cost_entry": {"cost": 0.01}
        }
        
        orch = WorkbenchOrchestrator({}, proxy=mock_proxy_inst)
        res = orch.process_request("hello")
        
        assert res["session_id"] == "s123"
        assert res["response"] == "AI Response"
        assert res["routing"]["model"] == "gpt-4"
        assert "src/main.py" in res["knowledge_used"]
        
        # Verify interactions
        mock_ctx_inst.add_to_history.assert_any_call("s123", "user", "hello")
        mock_mem_inst.remember.assert_called()
