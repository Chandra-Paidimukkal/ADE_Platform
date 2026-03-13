"""
Custom / stub provider adapter.
Copy this file and implement `complete()` to plug in any LLM.
"""
from __future__ import annotations

from backend.app.core.exceptions import AIProviderError
from backend.app.providers.base import BaseProvider


class CustomProvider(BaseProvider):
    """
    Template for a custom provider.
    Override __init__ to configure credentials/connection,
    and complete() to call your model.
    """

    def __init__(self) -> None:
        # Configure your connection here
        raise AIProviderError(
            "CustomProvider is a template – implement __init__ and complete()."
        )

    def complete(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        # Call your model here and return the raw text response
        raise NotImplementedError
