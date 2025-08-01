"""Interfaces for document indexing."""

from abc import ABC, abstractmethod
from typing import Iterable, Any


class Indexer(ABC):
    """Abstract base class for indexing documents in a knowledge store."""

    @abstractmethod
    def add(self, documents: Iterable[Any]) -> None:
        """Add one or multiple documents to the index."""

    @abstractmethod
    def delete(self, document_ids: Iterable[str]) -> None:
        """Remove documents identified by the given IDs from the index."""
