"""Concrete adapter implementations using `llama_index`.

The adapter layer bridges the abstract interfaces defined in
``core.interfaces`` with the concrete capabilities provided by the
`llama_index` library.  Only a very small subset of ``llama_index`` is used
and all configuration is sourced from environment variables so behaviour
can be tuned without code changes.
"""

from __future__ import annotations

import hashlib
import math
import os
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, List, Sequence

from core.interfaces.evaluator import Evaluator
from core.interfaces.indexer import Indexer
from core.interfaces.response_generator import ResponseGenerator
from core.interfaces.retriever import Retriever

try:  # pragma: no cover - optional dependency
    from llama_index.core import (
        PromptHelper,
        Settings,
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
        get_response_synthesizer,
        load_index_from_storage,
    )
    from llama_index.core.embeddings import BaseEmbedding
    from llama_index.readers.file import ImageReader, PDFReader

    try:  # pragma: no cover - optional Ollama support
        from llama_index.llms.ollama import Ollama
    except Exception:  # pragma: no cover - legacy path or missing
        try:
            from llama_index.legacy.llms.ollama import (
                Ollama,  # type: ignore[assignment]
            )
        except Exception:  # pragma: no cover - handled gracefully if missing
            Ollama = None  # type: ignore[assignment]
except Exception:  # pragma: no cover - handled gracefully if missing
    PromptHelper = Settings = SimpleDirectoryReader = StorageContext = None  # type: ignore[assignment]
    VectorStoreIndex = load_index_from_storage = get_response_synthesizer = None  # type: ignore[assignment]
    ImageReader = PDFReader = Ollama = None  # type: ignore[assignment]


class HashingEmbedding(BaseEmbedding):
    """Light-weight deterministic embedding based on token hashing."""

    dim: int = 256

    def __init__(self, dim: int = 256) -> None:
        super().__init__(dim=dim)

    def _hash(self, token: str) -> int:
        return int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in text.lower().split():
            vec[self._hash(token) % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm:
            vec = [v / norm for v in vec]
        return vec

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._embed(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._embed(text)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._embed(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]


def _configure_settings_from_env() -> None:
    """Configure global :class:`Settings` from environment variables."""

    if PromptHelper is None or Settings is None:
        raise ImportError("llama_index is required")

    env = os.environ
    chunk_size = int(env.get("CHUNK_SIZE", 800))
    chunk_overlap = float(env.get("CHUNK_OVERLAP", 0.1))
    context_window = int(env.get("MAX_INPUT_SIZE", 4096))
    num_output = int(env.get("NUM_OUTPUT", 512))

    prompt_helper = PromptHelper(
        context_window=context_window,
        num_output=num_output,
        chunk_overlap_ratio=chunk_overlap,
        chunk_size_limit=chunk_size,
    )

    if Ollama is None:  # pragma: no cover - optional dependency missing
        raise RuntimeError("Ollama LLM is not available")

    llm: Any
    base_url = env.get("OLLAMA_API_URL", "http://localhost:11434")
    try:  # pragma: no branch - optional
        llm = Ollama(
            model=env.get("LLM_MODEL", "llama3.1:latest"),
            base_url=base_url,
            temperature=float(env.get("TEMPERATURE", 0.1)),
            request_timeout=float(env.get("LLM_REQUEST_TIMEOUT", 120.0)),
        )
        # verify the Ollama server is reachable
        llm.client.list()
    except Exception as exc:  # pragma: no cover - network or init failure
        raise RuntimeError(
            f"Failed to connect to Ollama server at {base_url}"
        ) from exc

    embed_dim = int(env.get("EMBED_DIM", 256))
    embed_model = HashingEmbedding(dim=embed_dim)

    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.prompt_helper = prompt_helper


class LlamaIndexIndexer(Indexer):
    """Build and persist a :class:`VectorStoreIndex` from documents."""

    def __init__(self) -> None:
        _configure_settings_from_env()

    def build(
        self, docs_dir: Path, persist_dir: Path
    ) -> Any:  # pragma: no cover - heavy IO
        if SimpleDirectoryReader is None or VectorStoreIndex is None:
            raise ImportError("llama_index is required")

        file_extractor = {}
        if PDFReader is not None:
            file_extractor[".pdf"] = PDFReader()
        if ImageReader is not None:
            try:  # pragma: no cover - optional heavy dependency
                image_reader = ImageReader(parse_text=True)
            except Exception:  # pragma: no cover - missing deps
                image_reader = None
            if image_reader is not None:
                file_extractor.update(
                    {
                        ".png": image_reader,
                        ".jpg": image_reader,
                        ".jpeg": image_reader,
                    }
                )

        reader = SimpleDirectoryReader(
            str(docs_dir), file_extractor=file_extractor or None
        )
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents)

        index.storage_context.persist(persist_dir=str(persist_dir))
        return index

    @staticmethod
    def load(persist_dir: Path) -> Any:
        """Load a previously persisted index from ``persist_dir``."""

        if StorageContext is None or load_index_from_storage is None:
            raise ImportError("llama_index storage components are required")

        # Reconfigure Settings so the loaded index
        # retains the configured LLM instead of falling back to the
        # ``MockLLM`` placeholder which results in the
        # "LLM is explicitly disabled" warning.
        _configure_settings_from_env()

        storage = StorageContext.from_defaults(persist_dir=str(persist_dir))
        return load_index_from_storage(storage)


class LlamaIndexRetriever(Retriever):
    """Retrieve relevant nodes from a :class:`VectorStoreIndex`."""

    def __init__(self, index: Any) -> None:
        self.index = index
        env = os.environ
        self.k = int(env.get("RETRIEVAL_K", 5))
        self.fetch_k = int(env.get("FETCH_K", 20))

    def retrieve(self, query: str, top_k: int | None = None) -> Sequence[Any]:
        if top_k is None:
            top_k = self.k
        retriever = self.index.as_retriever(
            similarity_top_k=top_k, vector_store_kwargs={"fetch_k": self.fetch_k}
        )
        return retriever.retrieve(query)


class LlamaIndexResponseGenerator(ResponseGenerator):
    """Generate answers from retrieved nodes using ``llama_index``."""

    def __init__(self, index: Any) -> None:
        env = os.environ
        self.thinking_steps = int(env.get("THINKING_STEPS", 1))
        self.response_mode = env.get("RESPONSE_MODE", "compact")
        temperature = float(env.get("TEMPERATURE", 0.1))

        llm = Settings.llm
        if hasattr(llm, "temperature"):
            llm.temperature = temperature

        self.synthesizer = get_response_synthesizer(
            llm=llm,
            prompt_helper=Settings.prompt_helper,
            response_mode=self.response_mode,
        )

    def generate(self, query: str, documents: Sequence[Any]) -> str:
        if self.thinking_steps > 1:
            query = f"Think in {self.thinking_steps} steps and answer.\n{query}"
        response = self.synthesizer.synthesize(query, documents)
        return str(response)


class LlamaIndexEvaluator(Evaluator):
    """Compare two strings using :class:`difflib.SequenceMatcher`."""

    def evaluate(self, answer: str, expected: str) -> float:
        return SequenceMatcher(None, expected, answer).ratio()
