"""GPU monitoring module for NVIDIA T600 and other cards."""

import subprocess
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Monitors GPU utilization, memory, and temperature using nvidia-smi."""

    def __init__(self, host: Optional[str] = None, user: Optional[str] = None) -> None:
        self.host = host
        self.user = user
        self.available = self._check_nvidia_smi()

    def _get_ssh_prefix(self) -> List[str]:
        """Generate the SSH command prefix with proper options."""
        if not self.host:
            return []
        target = f"{self.user}@{self.host}" if self.user else str(self.host)
        prefix: List[str] = [
            "ssh",
            "-o", "ConnectTimeout=3",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            target
        ]
        return prefix

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available (locally or remotely)."""
        if self.host:
            cmd = self._get_ssh_prefix() + ["nvidia-smi -L"]
        else:
            cmd = ["nvidia-smi", "-L"]
            
        try:
            subprocess.run(cmd, capture_output=True, check=True, text=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            if self.host:
                logger.debug(f"Could not connect to GPU host {self.host} (user: {self.user}) via SSH")
            else:
                logger.debug("nvidia-smi not found locally")
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
            query_str = "nvidia-smi --query-gpu=gpu_name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits"
            
            if self.host:
                cmd = self._get_ssh_prefix() + [query_str]
            else:
                cmd = query_str.split()
                
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            # Simple single GPU parsing for now
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            
            if len(parts) >= 5:
                mem_used = int(parts[2])
                mem_total = int(parts[3])
                mem_percent = round(float(mem_used) / float(mem_total) * 100.0, 1) if mem_total > 0 else 0.0
                
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
