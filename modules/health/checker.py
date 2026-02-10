import logging
import time
from typing import Any, Dict, List, Optional
import requests

from modules.base import LodestarPlugin, EventBus

logger = logging.getLogger(__name__)


class HealthChecker(LodestarPlugin):
    """Monitors health of Lodestar components (Router, Ollama, External APIs)."""

    def __init__(self, config: Dict[str, Any], event_bus: Optional[EventBus] = None) -> None:
        super().__init__(config)
        self.event_bus = event_bus
        self.router_url = config.get("router_url", "http://localhost:4000")
        self.router_path = config.get("router_health_path", "/health")
        self.ollama_url = config.get("ollama_url", "http://192.168.120.211:11434")
        self.gpu_host = config.get("gpu_ssh_host")
        self.gpu_user = config.get("gpu_ssh_user")
        self.timeout = config.get("timeout", 2.0)
        self._last_status: Dict[str, Any] = {}
        
        # Initialize GPU monitor if possible
        from modules.health.gpu import GPUMonitor
        self.gpu_monitor = GPUMonitor(host=self.gpu_host, user=self.gpu_user)

    def start(self) -> None:
        """Start the health checker."""
        logger.info("HealthChecker started")
        # In a real async implementation, this would start a background task.
        # For now, checks are on-demand via health_check().

    def stop(self) -> None:
        """Stop the health checker."""
        logger.info("HealthChecker stopped")

    def health_check(self) -> Dict[str, Any]:
        """Perform on-demand health check of all components."""
        status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {}
        }

        # Check Router (LiteLLM)
        router_status = self._check_url(f"{self.router_url}{self.router_path}", "router")
        status["components"]["router"] = router_status

        # Check Ollama
        ollama_status = self._check_url(f"{self.ollama_url}/api/tags", "ollama")
        status["components"]["ollama"] = ollama_status

        # Check GPU
        gpu_status = self.gpu_monitor.check()
        status["components"]["gpu"] = gpu_status

        # Determine overall status
        if router_status["status"] == "down" or ollama_status["status"] == "down":
            status["status"] = "down"
        elif router_status["status"] == "degraded" or ollama_status["status"] == "degraded":
            status["status"] = "degraded"

        self._last_status = status
        
        if self.event_bus:
            self.event_bus.publish("health_checked", status)
            
        return status

    def _check_url(self, url: str, name: str) -> Dict[str, Any]:
        """Ping a URL to check availability."""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=2.0)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "code": 200
                }
            else:
                return {
                    "status": "degraded",
                    "latency_ms": round(latency, 2),
                    "code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "down",
                "error": str(e)
            }
