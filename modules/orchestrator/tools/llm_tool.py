"""LLM Tool — executes tasks by calling an LLM via LodestarProxy.

Routes tasks through the existing routing/fallback/cost-tracking
pipeline, so all routing rules and cost savings apply automatically.
"""

from typing import Any, Dict, List, Optional
import logging

from modules.orchestrator.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

# Default cost estimates per model (USD per 1k tokens, averaged input+output)
_MODEL_COST_PER_1K = {
    "gpt-3.5-turbo": 0.0,       # Ollama / free local
    "local-llama": 0.0,
    "deepseek-coder": 0.0,
    "claude-sonnet": 0.009,     # ~$3 input + $15 output / 2M avg tokens
    "claude-opus": 0.030,
    "gpt-4o": 0.010,
    "gpt-4o-mini": 0.001,
}

_LLM_CAPABILITIES = [
    "code_generation",
    "code_review",
    "architecture",
    "documentation",
    "bug_fix",
    "refactor",
    "planning",
    "synthesis",
    "general",
]


class LLMTool(Tool):
    """Executes a task by sending a prompt to an LLM via LodestarProxy.

    The tool optionally accepts a model_hint to prefer a specific model.
    Without a hint the SemanticRouter picks the cheapest capable model.

    Args:
        proxy: LodestarProxy instance for routing and execution.
        model_hint: Optional model name override (e.g. 'claude-sonnet').
        name: Human-readable tool name for logging.
    """

    def __init__(self, proxy: Any, model_hint: Optional[str] = None, name: str = "llm") -> None:
        self.proxy = proxy
        self.model_hint = model_hint
        self.name = name

    # ------------------------------------------------------------------
    # Tool interface
    # ------------------------------------------------------------------

    def can_handle(self, task: Dict[str, Any]) -> bool:
        cap = task.get("capability", "")
        return cap in _LLM_CAPABILITIES or task.get("tool_type") == "llm"

    def get_capabilities(self) -> List[str]:
        return list(_LLM_CAPABILITIES)

    def estimate_cost(self, task: Dict[str, Any]) -> float:
        model = self.model_hint or task.get("preferred_model", "gpt-3.5-turbo")
        prompt = task.get("prompt", "")
        estimated_tokens = max(len(prompt.split()) * 1.3, 200)  # rough estimate
        return _MODEL_COST_PER_1K.get(model, 0.005) * (estimated_tokens / 1000)

    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Build prompt from task + context and call LodestarProxy."""
        prompt = self._build_prompt(task, context)

        model_override = self.model_hint or task.get("preferred_model")
        task_override = task.get("capability")

        # Use a simple callable that returns the prompt itself (dry-run)
        # In production this would call the actual LiteLLM proxy
        def request_fn(model: str) -> str:
            try:
                import requests
                resp = requests.post(
                    "http://localhost:4000/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": task.get("max_tokens", 4096),
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as exc:
                raise RuntimeError(f"LLM call failed: {exc}") from exc

        try:
            result = self.proxy.handle_request(
                prompt=prompt,
                request_fn=request_fn,
                task_override=task_override,
                model_override=model_override,
            )

            response_text = ""
            if result.get("result") and result["result"].success:
                response_text = result["result"].response or ""

            output_key = task.get("output", "response")
            return ToolResult(
                success=True,
                output=response_text,
                artifacts={output_key: response_text},
                cost=result.get("cost_entry", {}).get("cost", 0.0),
                metadata={"model": result.get("model", "unknown")},
            )

        except Exception as exc:
            logger.exception("LLMTool execution failed for task %s", task.get("name"))
            return ToolResult(
                success=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, task: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Substitute {artifact_name} placeholders in task prompt with context."""
        raw = task.get("prompt", "")
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in raw:
                raw = raw.replace(placeholder, str(value))
        return raw
