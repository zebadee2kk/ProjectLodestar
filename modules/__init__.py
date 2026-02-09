"""
ProjectLodestar v2 module system.

All v2 features are self-contained modules that can be independently
enabled, disabled, and tested. Modules depend on the base plugin
interface but never on each other.
"""

from modules.base import LodestarPlugin, EventBus

__all__ = ["LodestarPlugin", "EventBus"]
