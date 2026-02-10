"""GPU monitoring module for NVIDIA T600 and other cards."""

import subprocess
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Monitors GPU utilization, memory, and temperature using nvidia-smi."""

    def __init__(self) -> None:
        self.available = self._check_nvidia_smi()

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available in the system."""
        try:
            subprocess.run(["nvidia-smi", "-L"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("nvidia-smi not found or failed, GPU monitoring disabled")
            return False

    def check(self) -> Dict[str, Any]:
        """Perform a GPU health check and return metrics.
        
        Returns:
            Dict containing status and metrics (utilization, memory, temp).
        """
        if not self.available:
            return {"status": "not_available"}

        try:
            # query-gpu=gpu_name,utilization.gpu,memory.used,memory.total,temperature.gpu
            cmd = [
                "nvidia-smi",
                "--query-gpu=gpu_name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Simple single GPU parsing for now
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            
            if len(parts) >= 5:
                mem_used = int(parts[2])
                mem_total = int(parts[3])
                mem_percent = round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0
                
                return {
                    "status": "healthy",
                    "name": parts[0],
                    "load_pct": int(parts[1]),
                    "memory_used_mb": mem_used,
                    "memory_total_mb": mem_total,
                    "memory_pct": mem_percent,
                    "temp_c": int(parts[4])
                }
            
            return {"status": "degraded", "error": "Unexpected nvidia-smi output format"}

        except Exception as e:
            logger.error(f"Error checking GPU health: {e}")
            return {"status": "down", "error": str(e)}
