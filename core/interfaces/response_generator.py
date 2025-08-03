"""Core interface for turning retrieved context into an answer."""

from abc import ABC, abstractmethod
from typing import Any, Sequence


class ResponseGenerator(ABC):
    """Abstract base class for generating responses."""

    @abstractmethod
    def generate(self, query: str, documents: Sequence[Any]) -> str:
        """Return an answer to ``query`` based on ``documents``."""
