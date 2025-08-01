"""Interfaces for retrieving documents relevant to a query."""

from abc import ABC, abstractmethod
from typing import Sequence


class Retriever(ABC):
    """Abstract base class for retrieving relevant documents."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> Sequence[str]:
        """Return up to ``top_k`` documents relevant to ``query``."""
