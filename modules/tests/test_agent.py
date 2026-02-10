import pytest
from unittest.mock import MagicMock, patch
from modules.agent.executor import AgentExecutor
from modules.routing.proxy import LodestarProxy
import subprocess

class TestAgentExecutor:
    @pytest.fixture
    def mock_proxy(self):
        proxy = MagicMock(spec=LodestarProxy)
        return proxy

    def test_run_command_success(self, mock_proxy):
        executor = AgentExecutor(mock_proxy)
        result = executor.run_command("echo hello")
        assert result["success"] is True
        assert "hello" in result["output"]

    @patch("subprocess.run")
    def test_run_command_failure_retry(self, mock_subprocess, mock_proxy):
        # Mock subprocess to fail first, then succeed
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "bad_cmd", stderr="SyntaxError"),
            MagicMock(stdout="Success output")
        ]
        
        # Mock LLM to return a fixed command
        mock_result = MagicMock()
        mock_result.result.success = True
        mock_result.result.response = "fixed_cmd"
        mock_proxy.handle_request.return_value = {"result": mock_result.result}
        
        executor = AgentExecutor(mock_proxy)
        result = executor.run_command("bad_cmd")
        
        assert result["success"] is True
        assert result["output"] == "Success output"
        # Attempts: 1. bad_cmd (fail), 2. fixed_cmd (success)
        assert len(result["attempts"]) == 2
        assert result["attempts"][0][0] == "bad_cmd"
        assert result["attempts"][1][0] == "fixed_cmd"

    @patch("subprocess.run")
    def test_run_command_max_retries(self, mock_subprocess, mock_proxy):
        # Always fail
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "bad_cmd", stderr="Error")
        
        # Mock LLM always returns a fix attempt
        mock_result = MagicMock()
        mock_result.result.success = True
        mock_result.result.response = "fix_attempt"
        mock_proxy.handle_request.return_value = {"result": mock_result.result}
        
        executor = AgentExecutor(mock_proxy, max_retries=2)
        result = executor.run_command("bad_cmd")
        
        assert result["success"] is False
        # Initial + 2 retries = 3 attempts total attempted but the loop runs max_retries+1 times?
        # range(3) -> 0, 1, 2.
        # 0: bad_cmd. LLM -> fix_attempt.
        # 1: fix_attempt. LLM -> fix_attempt.
        # 2: fix_attempt. Fail. Max retries exceeded.
        assert len(result["attempts"]) == 3
