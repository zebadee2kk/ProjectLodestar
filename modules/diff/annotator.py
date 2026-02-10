from typing import Any, Dict, List, Optional, Tuple
import logging

from modules.routing.proxy import LodestarProxy

logger = logging.getLogger(__name__)


class DiffAnnotator:
    """Generates AI annotations for diff blocks using LodestarProxy.

    Routes diff explanation tasks to the most cost-effective model
    via the semantic router.
    """

    def __init__(self, proxy: LodestarProxy):
        self.proxy = proxy

    def annotate(self, file_path: str, diff_lines: List[str]) -> Tuple[str, float]:
        """Generate an AI annotation for a set of diff lines.

        Args:
            file_path: Path of the file being changed.
            diff_lines: List of diff lines (prefixed with +, -, or space).

        Returns:
            Tuple of (annotation_text, confidence_score).
        """
        if not diff_lines:
            return "No changes detected", 1.0

        # Construct a prompt for the LLM
        diff_text = "\n".join(diff_lines)
        prompt = (
            f"Explain the following code change in {file_path}. "
            f"Be concise (max 1 sentence). Focus on the 'why' and 'what'.\n\n"
            f"Diff:\n{diff_text}"
        )

        try:
            # Route to a model optimized for simple code explanation
            # We explicitly override the task to 'code_explanation' to ensure
            # it routes correctly (likely to a cheaper model like Llama/GPT-4o-mini)
            response = self.proxy.handle_request(
                prompt=prompt,
                task_override="code_explanation",
                live=True
            )

            if response["result"].success and response["result"].response:
                explanation = response["result"].response.strip()
                # Confidence is hard to get from simple completion, simplified to 0.9
                # In future we could ask model for confidence
                return explanation, 0.9
            else:
                logger.warning("LLM failed to explain diff")
                return self._fallback_heuristic(diff_lines)

        except Exception as e:
            logger.error(f"Error calling LLM for annotation: {e}")
            return self._fallback_heuristic(diff_lines)

    def _fallback_heuristic(self, lines: List[str]) -> Tuple[str, float]:
        """Simple heuristic fallback if LLM fails."""
        added = [l for l in lines if l.startswith("+")]
        removed = [l for l in lines if l.startswith("-")]

        if added and not removed:
            return f"Added {len(added)} line(s)", 0.5
        elif removed and not added:
            return f"Removed {len(removed)} line(s)", 0.5
        else:
            return "Modified logic", 0.5
