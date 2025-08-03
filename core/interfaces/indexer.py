"""Core interface for building a document index.

This repository aims to keep a clean separation between the high level
application code and the underlying libraries used to implement the RAG
pipeline.  The :class:`Indexer` defines the minimal contract required by
the ingestion service.  Concrete implementations (for example the
``LlamaIndexIndexer``) are free to store whatever state they need as long
as they honour this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Indexer(ABC):
    """Abstract base class responsible for creating and persisting an index."""

    @abstractmethod
    def build(self, docs_dir: Path, persist_dir: Path) -> Any:
        """Build or update the index from ``docs_dir`` and persist it.

        Parameters
        ----------
        docs_dir:
            Directory containing the source documents.
        persist_dir:
            Directory where the index should be stored.

        Returns
        -------
        Any
            An implementation defined handle to the created index.
        """
