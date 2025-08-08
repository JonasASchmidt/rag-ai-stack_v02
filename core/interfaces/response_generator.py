"""Core interface for turning retrieved context into an answer."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Sequence


class ResponseGenerator(ABC):
    """Abstract base class for generating responses."""

    @abstractmethod
    def generate(self, query: str, documents: Sequence[Any]) -> str:
        """Return an answer to ``query`` based on ``documents``."""

    def generate_stream(
        self, query: str, documents: Sequence[Any]
    ) -> Iterator[str]:
        """Yield tokens for the answer.

        The default implementation falls back to :meth:`generate`.
        Implementations that support token streaming should override this.
        """

        yield self.generate(query, documents)

    async def agenerate_stream(
        self, query: str, documents: Sequence[Any]
    ) -> AsyncIterator[str]:
        """Asynchronously yield tokens for the answer.

        This implementation simply iterates over the synchronous
        :meth:`generate_stream`.  Subclasses can override it with a truly
        asynchronous variant.
        """

        for token in self.generate_stream(query, documents):
            yield token
