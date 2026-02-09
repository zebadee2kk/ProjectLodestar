"""Diff preview renderer with AI annotation support.

Parses unified diffs and structures them into annotatable blocks
that can carry AI reasoning and confidence scores.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from modules.base import LodestarPlugin

logger = logging.getLogger(__name__)


@dataclass
class DiffBlock:
    """A single block of changed lines in a diff.

    Attributes:
        file_path: Path of the file being changed.
        old_start: Starting line number in the old file.
        new_start: Starting line number in the new file.
        lines: Raw diff lines (prefixed with +, -, or space).
        annotation: Optional AI explanation of the change.
        confidence: AI confidence score (0.0 to 1.0).
    """

    file_path: str
    old_start: int
    new_start: int
    lines: List[str] = field(default_factory=list)
    annotation: Optional[str] = None
    confidence: Optional[float] = None


class DiffPreview(LodestarPlugin):
    """Parses and renders diffs with AI annotations.

    Args:
        config: Module configuration.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._started = False

    def start(self) -> None:
        """Start the diff preview module."""
        if not self.enabled:
            logger.info("Diff preview module disabled, skipping start")
            return
        self._started = True
        logger.info("Diff preview module started")

    def stop(self) -> None:
        """Stop the diff preview module."""
        self._started = False
        logger.info("Diff preview module stopped")

    def health_check(self) -> Dict[str, Any]:
        """Return module health status."""
        return {
            "status": "healthy" if self._started else "down",
            "enabled": self.enabled,
        }

    def parse_unified_diff(self, diff_text: str) -> List[DiffBlock]:
        """Parse a unified diff string into structured DiffBlocks.

        Args:
            diff_text: Raw unified diff output (e.g. from git diff).

        Returns:
            List of DiffBlock objects, one per hunk.
        """
        blocks: List[DiffBlock] = []
        current_file = ""
        current_block: Optional[DiffBlock] = None

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("@@ "):
                # Parse hunk header: @@ -old_start,count +new_start,count @@
                if current_block is not None:
                    blocks.append(current_block)
                old_start, new_start = self._parse_hunk_header(line)
                current_block = DiffBlock(
                    file_path=current_file,
                    old_start=old_start,
                    new_start=new_start,
                )
            elif current_block is not None and line and line[0] in ("+", "-", " "):
                current_block.lines.append(line)

        if current_block is not None:
            blocks.append(current_block)

        return blocks

    def annotate_block(
        self, block: DiffBlock, annotation: str, confidence: float
    ) -> DiffBlock:
        """Attach an AI annotation and confidence score to a diff block.

        Args:
            block: The DiffBlock to annotate.
            annotation: AI-generated explanation.
            confidence: Confidence score between 0.0 and 1.0.

        Returns:
            The same block with annotation and confidence set.

        Raises:
            ValueError: If confidence is not in [0.0, 1.0].
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {confidence}"
            )
        block.annotation = annotation
        block.confidence = confidence
        return block

    def format_block(self, block: DiffBlock) -> str:
        """Format a DiffBlock as a readable string with optional annotation.

        Args:
            block: The DiffBlock to format.

        Returns:
            Formatted string representation.
        """
        header = f"--- {block.file_path} (lines {block.old_start}→{block.new_start})"
        parts = [header]

        for line in block.lines:
            parts.append(f"  {line}")

        if block.annotation:
            conf_str = (
                f" [{block.confidence:.0%}]" if block.confidence is not None else ""
            )
            parts.append(f"  # AI{conf_str}: {block.annotation}")

        return "\n".join(parts)

    @staticmethod
    def _parse_hunk_header(header: str) -> tuple:
        """Extract old_start and new_start from a hunk header line.

        Args:
            header: Line like '@@ -10,5 +12,7 @@'

        Returns:
            Tuple of (old_start, new_start).
        """
        # Strip @@ markers and any trailing context
        parts = header.split("@@")[1].strip()
        ranges = parts.split()
        old_start = int(ranges[0].split(",")[0].lstrip("-"))
        new_start = int(ranges[1].split(",")[0].lstrip("+"))
        return old_start, new_start
