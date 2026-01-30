"""Core protocols and interfaces for Conduit."""

from conduit.core.protocols import Capabilities, ChatModel, Embeddable, ModelInfo

__all__ = [
    "ChatModel",
    "Embeddable",
    "ModelInfo",
    "Capabilities",
]
