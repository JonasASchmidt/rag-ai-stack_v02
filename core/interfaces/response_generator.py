"""Interfaces for generating answers from retrieved context."""

from abc import ABC, abstractmethod
from typing import Sequence


class ResponseGenerator(ABC):
    """Abstract base class for generating responses based on retrieved documents."""

    @abstractmethod
    def generate(self, query: str, documents: Sequence[str]) -> str:
        """Generate a response for ``query`` using the given ``documents``."""
