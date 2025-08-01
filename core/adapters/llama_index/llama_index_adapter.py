"""LlamaIndex adapter classes.

This module provides concrete classes to index documents, retrieve nodes,
produce responses, and evaluate results using the LlamaIndex library.

Configuration is pulled from environment variables to allow flexible
runtime tuning without code changes.
"""

from __future__ import annotations

import os
from typing import Any, List

try:  # pragma: no cover - optional dependency
    from llama_index import ServiceContext  # type: ignore
    from llama_index import PromptHelper, SimpleDirectoryReader, VectorStoreIndex
    from llama_index.evaluation import EmbeddingSimilarityEvaluator  # type: ignore
    from llama_index.readers.file import ImageReader, PDFReader  # type: ignore
except Exception:  # pragma: no cover - handled gracefully if missing
    PromptHelper = ServiceContext = SimpleDirectoryReader = VectorStoreIndex = None  # type: ignore
    EmbeddingSimilarityEvaluator = ImageReader = PDFReader = None  # type: ignore


def _prompt_helper_from_env() -> Any:
    """Create a ``PromptHelper`` configured from environment variables.

    The following variables are recognised:

    ``LLAMA_PROMPT_MAX_INPUT_SIZE``
        Maximum number of tokens that may be passed to the model.
    ``LLAMA_PROMPT_NUM_OUTPUT``
        Maximum number of tokens the model may generate.
    ``LLAMA_PROMPT_MAX_CHUNK_OVERLAP``
        Overlap between chunks when splitting documents.
    ``LLAMA_PROMPT_CHUNK_SIZE_LIMIT``
        Upper bound for chunk size when splitting documents.
    """

    max_input_size = int(os.environ.get("LLAMA_PROMPT_MAX_INPUT_SIZE", 4096))
    num_output = int(os.environ.get("LLAMA_PROMPT_NUM_OUTPUT", 256))
    max_chunk_overlap = int(os.environ.get("LLAMA_PROMPT_MAX_CHUNK_OVERLAP", 20))
    chunk_size_limit = int(os.environ.get("LLAMA_PROMPT_CHUNK_SIZE_LIMIT", 600))

    if PromptHelper is None:
        raise ImportError("llama_index is required for PromptHelper")

    return PromptHelper(
        max_input_size=max_input_size,
        num_output=num_output,
        max_chunk_overlap=max_chunk_overlap,
        chunk_size_limit=chunk_size_limit,
    )


class LlamaIndexIndexer:
    """Index documents using LlamaIndex.

    Parameters are sourced from environment variables via ``PromptHelper``.
    OCR is enabled for PDFs and common image formats.
    """

    def __init__(self) -> None:
        prompt_helper = _prompt_helper_from_env()
        if ServiceContext is None:
            raise ImportError("llama_index is required for ServiceContext")

        self.service_context = ServiceContext.from_defaults(prompt_helper=prompt_helper)

    def index(self, path: str) -> Any:
        """Create a ``VectorStoreIndex`` for files located at ``path``."""

        if SimpleDirectoryReader is None or VectorStoreIndex is None:
            raise ImportError("llama_index is required for indexing")
        if ImageReader is None or PDFReader is None:
            raise ImportError("llama_index file readers are required")

        file_extractor = {
            ".pdf": PDFReader(ocr=True),
            ".png": ImageReader(ocr=True),
            ".jpg": ImageReader(ocr=True),
            ".jpeg": ImageReader(ocr=True),
        }
        reader = SimpleDirectoryReader(path, file_extractor=file_extractor)
        documents = reader.load_data()
        return VectorStoreIndex.from_documents(
            documents, service_context=self.service_context
        )


class LlamaIndexRetriever:
    """Retrieve relevant nodes from a ``VectorStoreIndex``."""

    def __init__(self, index: Any) -> None:
        self.index = index
        env = os.environ
        self.k = int(env.get("LLAMA_RETRIEVER_K", 4))
        self.fetch_k = int(env.get("LLAMA_RETRIEVER_FETCH_K", 20))

    def retrieve(self, query: str) -> List[Any]:
        """Retrieve nodes matching ``query``."""

        retriever = self.index.as_retriever(
            similarity_top_k=self.k, vector_store_kwargs={"fetch_k": self.fetch_k}
        )
        return retriever.retrieve(query)


class LlamaIndexResponseGenerator:
    """Generate responses for queries using a ``VectorStoreIndex``."""

    def __init__(self, index: Any) -> None:
        self.query_engine = index.as_query_engine()

    def generate(self, query: str) -> str:
        """Generate a textual answer for ``query``."""

        response = self.query_engine.query(query)
        return str(response)


class LlamaIndexEvaluator:
    """Evaluate responses using embedding similarity."""

    def __init__(self) -> None:
        if EmbeddingSimilarityEvaluator is None:
            raise ImportError("llama_index evaluator components are required")
        self.evaluator = EmbeddingSimilarityEvaluator()

    def evaluate(self, response: str, reference: str) -> Any:
        """Return an evaluation score between ``response`` and ``reference``."""

        return self.evaluator.evaluate(response=response, reference=reference)
