"""Intelligent task-based routing module.

Routes LLM requests to the most appropriate model based on task
classification, tag-based rules, and configurable fallback chains.
"""

from modules.routing.router import SemanticRouter

__all__ = ["SemanticRouter"]
