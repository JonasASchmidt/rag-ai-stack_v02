"""Concrete adapter implementations using `llama_index`.

The adapter layer bridges the abstract interfaces defined in
``core.interfaces`` with the concrete capabilities provided by the
`llama_index` library.  Only a very small subset of ``llama_index`` is used
and all configuration is sourced from environment variables so behaviour
can be tuned without code changes.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import subprocess
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, List, Sequence

from core.interfaces.evaluator import Evaluator
from core.interfaces.indexer import Indexer
from core.interfaces.response_generator import ResponseGenerator
from core.interfaces.retriever import Retriever

logger = logging.getLogger(__name__)

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
    from llama_index.core.llms.mock import MockLLM
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
    ImageReader = PDFReader = Ollama = MockLLM = None  # type: ignore[assignment]

    class BaseEmbedding:  # pragma: no cover - minimal fallback
        def __init__(self, dim: int = 256) -> None:
            self.dim = dim


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

    llm: Any
    base_url = env.get("OLLAMA_API_URL", "http://localhost:11434")
    model_name = env.get("LLM_MODEL", "llama3.1:latest")

    if Ollama is None:  # pragma: no cover - optional dependency missing
        logger.warning("Ollama LLM is not available, using MockLLM")
        llm = MockLLM()
    else:
        additional_kwargs = {
            "num_ctx": int(env.get("OLLAMA_NUM_CTX", "2048")),
            "num_batch": int(env.get("OLLAMA_NUM_BATCH", "16")),
            "num_predict": int(env.get("OLLAMA_NUM_PREDICT", "512")),
        }
        llm_kwargs = {
            "model": model_name,
            "base_url": base_url,
            "temperature": float(env.get("TEMPERATURE", 0.1)),
            "request_timeout": float(env.get("LLM_REQUEST_TIMEOUT", 120.0)),
            "keep_alive": env.get("OLLAMA_KEEP_ALIVE", "5m"),
            "additional_kwargs": additional_kwargs,
        }
        try:  # pragma: no branch - optional
            llm = Ollama(**llm_kwargs)
            # verify the Ollama server is reachable
            llm.client.list()
        except Exception as exc:  # pragma: no cover - network or init failure
            auto_start = env.get("OLLAMA_AUTO_START")
            if auto_start:
                logger.info(
                    "Failed to connect to Ollama server at %s: %s. Attempting to start it.",
                    base_url,
                    exc,
                )
                try:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as start_exc:
                    logger.warning(
                        "Unable to start Ollama server: %s; falling back to MockLLM",
                        start_exc,
                    )
                    llm = MockLLM()
                else:
                    timeout = float(env.get("OLLAMA_STARTUP_TIMEOUT", "30"))
                    deadline = time.time() + timeout
                    while time.time() < deadline:
                        try:
                            time.sleep(1)
                            llm = Ollama(**llm_kwargs)
                            llm.client.list()
                            break
                        except Exception:
                            continue
                    else:
                        logger.warning(
                            "Ollama server did not start within %.0f seconds; falling back to MockLLM",
                            timeout,
                        )
                        llm = MockLLM()
            else:
                logger.warning(
                    "Failed to connect to Ollama server at %s: %s; falling back to MockLLM",
                    base_url,
                    exc,
                )
                llm = MockLLM()

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
            streaming=True,
        )

    def generate(self, query: str, documents: Sequence[Any]) -> str:
        if self.thinking_steps > 1:
            query = f"Think in {self.thinking_steps} steps and answer.\n{query}"
        response = self.synthesizer.synthesize(query, documents)
        return str(response)

    def generate_stream(
        self, query: str, documents: Sequence[Any]
    ) -> Iterator[str]:
        """Yield tokens from the synthesized response as they are produced."""

        if self.thinking_steps > 1:
            query = f"Think in {self.thinking_steps} steps and answer.\n{query}"
        response = self.synthesizer.synthesize(query, documents)
        gen = getattr(response, "response_gen", None)
        if gen is None:
            yield str(response)
        else:
            for token in gen:
                yield token

    async def agenerate_stream(
        self, query: str, documents: Sequence[Any]
    ) -> AsyncIterator[str]:
        """Asynchronously yield tokens from the synthesized response.

        Falls ``llama_index`` eine native asynchrone Streaming-Methode
        bereitstellt, wird diese genutzt. Andernfalls wird auf die
        synchrone :meth:`generate_stream`-Variante zurückgegriffen.
        """

        if self.thinking_steps > 1:
            query = f"Think in {self.thinking_steps} steps and answer.\n{query}"

        asynthesize = getattr(self.synthesizer, "asynthesize", None)
        if callable(asynthesize):
            response = await asynthesize(query, documents)
            agen = getattr(response, "async_response_gen", None)
            if agen is None:
                yield str(response)
            else:
                async for token in agen:
                    yield token
            return

        # Fallback: führe die synchrone Streaming-Methode aus.
        for token in self.generate_stream(query, documents):
            yield token


class LlamaIndexEvaluator(Evaluator):
    """Compare two strings using :class:`difflib.SequenceMatcher`."""

    def evaluate(self, answer: str, expected: str) -> float:
        return SequenceMatcher(None, expected, answer).ratio()
