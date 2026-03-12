"""Abstract base class for all AI provider adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """All provider adapters implement this interface."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        """Send prompt to the provider and return the raw text response."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
