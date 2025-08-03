"""Core interface for retrieving relevant pieces of information.

Concrete retrievers are expected to return lightweight objects (strings,
nodes, documents ...) that contain enough metadata so the
``ResponseGenerator`` can later craft an answer.  The interface stays very
small on purpose to remain agnostic of the underlying vector store or
retrieval mechanism used.
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence


class Retriever(ABC):
    """Abstract base class for retrieving relevant items from an index."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> Sequence[Any]:
        """Return up to ``top_k`` items relevant to ``query``."""
