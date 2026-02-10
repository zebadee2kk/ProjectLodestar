"""Agent executor for self-healing tool execution."""

import subprocess
import logging
from typing import Any, Dict, List, Optional
from modules.routing.proxy import LodestarProxy

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes commands with automatic error recovery.
    
    If a command fails, it consults the LodestarProxy (LLM) to diagnose
    the error and suggest a fix, then retries execution.
    """

    def __init__(self, proxy: LodestarProxy, max_retries: int = 3) -> None:
        self.proxy = proxy
        self.max_retries = max_retries

    def run_command(self, command: str) -> Dict[str, Any]:
        """Run a shell command with retry logic.
        
        Args:
            command: The command string to execute.
            
        Returns:
            Dict containing 'success', 'output', 'error', 'attempts'.
        """
        attempts = []
        current_command = command
        
        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempt {attempt+1}/{self.max_retries + 1}: {current_command}")
            
            try:
                # Capture output
                result = subprocess.run(
                    current_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Success
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": None,
                    "attempts": attempts + [(current_command, "Success")]
                }
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Exit code {e.returncode}\nStderr: {e.stderr}"
                attempts.append((current_command, error_msg))
                logger.warning(f"Command failed: {error_msg}")
                
                if attempt < self.max_retries:
                    # Ask LLM for a fix
                    fix_suggestion = self._get_fix_from_llm(current_command, error_msg)
                    if fix_suggestion:
                        logger.info(f"LLM suggested fix: {fix_suggestion}")
                        # Apply fix (run the suggestion, or update command)
                        # For simplicity, if the LLM suggests a NEW command to run instead, we use it.
                        # If it suggests a PRE-REQUISITE (like pip install), we run it, then retry original?
                        # Simplest heuristic: The LLM returns the command to run NEXT.
                        current_command = fix_suggestion
                    else:
                        logger.error("LLM could not suggest a fix.")
                        break
                else:
                    logger.error("Max retries exceeded.")

        return {
            "success": False,
            "output": None,
            "error": attempts[-1][1],
            "attempts": attempts
        }

    def _get_fix_from_llm(self, command: str, error: str) -> Optional[str]:
        """Ask LodestarProxy for a fix for the failed command."""
        prompt = (
            "You are a shell command optimization expert. A command just failed.\n\n"
            f"Original Goal/Command: {command}\n"
            f"Error Output: {error}\n\n"
            "Your Task: Provide ONLY the corrected shell command to achieve the goal.\n"
            "Rules:\n"
            "- NO explanations.\n"
            "- NO markdown code blocks.\n"
            "- NO conversational text.\n"
            "- Output ONLY the command string."
        )
        
        try:
            response = self.proxy.handle_request(
                prompt=prompt,
                task_override="code_generation",
                live=True
            )
            
            if response["result"].success and response["result"].response:
                # Handle LiteLLM ModelResponse or raw string
                res = response["result"].response
                content = ""
                if hasattr(res, "choices"):
                    content = res.choices[0].message.content
                elif isinstance(res, str):
                    content = res
                else:
                    content = str(res)
                
                # Cleanup: Take the last non-empty line that isn't conversational
                lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
                
                # Filter out markdown backticks
                lines = [l.replace("```bash", "").replace("```", "").strip() for l in lines]
                lines = [l for l in lines if l]

                if not lines:
                    return None

                # Optimization: Find a line that looks like a command
                fix = lines[-1] # Fallback
                for line in lines:
                    # Heuristic: commands don't usually start with sentence-starters like "The"
                    if any(cmd in line for cmd in ["du ", "find ", "ls ", "grep ", "|", "cat ", "echo "]):
                        if not any(line.lower().startswith(p) for p in ["the ", "it ", "here ", "this ", "you "]):
                            fix = line
                            break
                
                return fix
            return None
        except Exception as e:
            logger.error(f"Error consulting LLM: {e}")
            return None
