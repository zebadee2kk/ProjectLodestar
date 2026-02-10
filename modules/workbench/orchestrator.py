"""Workbench orchestrator for Project Lodestar.

Coordinates Memory, Context, and Knowledge modules to provide 
a persistent, project-aware AI working environment.
"""

from typing import Any, Dict, List, Optional
import logging
from modules.memory import MemoryModule
from modules.context import ContextModule
from modules.knowledge import KnowledgeModule

logger = logging.getLogger(__name__)


class WorkbenchOrchestrator:
    """Unifies persistent memory, project knowledge, and model routing.

    Args:
        config: Global module configuration.
        proxy: Optional LodestarProxy instance.
    """

    def __init__(self, config: Dict[str, Any], proxy: Optional[Any] = None) -> None:
        self.config = config
        
        # Initialize modules
        self.memory = MemoryModule(config.get("memory", {}))
        self.context = ContextModule(config.get("context", {}))
        self.knowledge = KnowledgeModule(config.get("knowledge", {}), memory_module=self.memory)
        
        # We also need the Proxy for final routing and execution
        if proxy:
            self.proxy = proxy
        else:
            from modules.routing.proxy import LodestarProxy
            self.proxy = LodestarProxy(config_dir="config")

    def start(self) -> None:
        """Start all sub-modules."""
        self.memory.start()
        self.context.start()
        self.knowledge.start()
        logger.info("WorkbenchOrchestrator started")

    def stop(self) -> None:
        """Stop all sub-modules."""
        self.memory.stop()
        self.context.stop()
        self.knowledge.stop()
        logger.info("WorkbenchOrchestrator stopped")

    def process_request(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a request using the full persistent workbench pipeline.

        1. Load/Create session.
        2. Retrieve relevant project knowledge.
        3. Retrieve relevant long-term memories.
        4. Assemble augmented prompt.
        5. Pass to Proxy for routing/execution.
        6. Store result in history and memory.
        """
        # 1. Session Management
        if not session_id:
            session_id = self.context.create_session("Auto Session")
        
        # 2. Knowledge Retrieval (RAG)
        knowledge_hits = self.knowledge.search(prompt, limit=3)
        knowledge_context = "\n".join([f"--- snippet from {h['metadata'].get('path')} ---\n{h['text']}" for h in knowledge_hits])
        
        # 3. Memory Retrieval
        memory_hits = self.memory.search(prompt, limit=2)
        memory_context = "\n".join([h['text'] for h in memory_hits])
        
        # 4. Prompt Assembly
        augmented_prompt = f"""CONTEXT FROM PROJECT KNOWLEDGE:
{knowledge_context}

LONG-TERM MEMORY:
{memory_context}

USER REQUEST:
{prompt}
"""
        # 5. Route and Execute via Proxy
        result = self.proxy.handle_request(augmented_prompt, live=True)
        
        # 6. Update Persistence
        response_text = "ERROR: No response"
        if result.get("result") and result["result"].success:
            # Depending on how LiteLLM response is structured
            resp = result["result"].response
            if hasattr(resp, "choices"):
                response_text = resp.choices[0].message.content
            else:
                response_text = str(resp)

        self.context.add_to_history(session_id, "user", prompt)
        self.context.add_to_history(session_id, "assistant", response_text)
        
        # Store significant interactions in long-term memory
        self.memory.remember(f"User asked: {prompt}\nAI responded: {response_text}", {"session_id": session_id})
        
        return {
            "session_id": session_id,
            "response": response_text,
            "routing": {
                "model": result.get("model"),
                "task": result.get("task"),
                "cost": result.get("cost_entry", {}).get("cost", 0)
            },
            "knowledge_used": [h['metadata'].get('path') for h in knowledge_hits]
        }

    def health_check(self) -> Dict[str, Any]:
        """Return health of all components."""
        return {
            "memory": self.memory.health_check(),
            "context": self.context.health_check(),
            "knowledge": self.knowledge.health_check(),
        }
