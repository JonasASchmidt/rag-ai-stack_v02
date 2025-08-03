"""Build or update the vector index used by the chat backend.

The indexer loads configuration from ``.env`` (if present) and reads files
from ``DOCS_DIR``.  Supported file types include Markdown, plain text,
PDFs and common image formats where OCR is applied.  The resulting
``VectorStoreIndex`` is persisted to ``INDEX_DIR`` so that the backend can
load it at startup.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from core.adapters.llama_index.llama_index_adapter import LlamaIndexIndexer


def build_index(docs_dir: Path, index_dir: Path) -> None:
    """Build or update the index for ``docs_dir`` and persist to ``index_dir``."""

    indexer = LlamaIndexIndexer()
    indexer.build(docs_dir, index_dir)


def main() -> None:  # pragma: no cover - CLI entry point
    load_dotenv()
    env = os.environ
    docs_dir = Path(env.get("DOCS_DIR", "docs"))
    index_dir = Path(env.get("INDEX_DIR", "vectorstore/llama"))

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logging.info("Starting ingestion from %s -> %s", docs_dir, index_dir)
    build_index(docs_dir, index_dir)
    logging.info("Ingestion finished")


if __name__ == "__main__":  # pragma: no cover - script behaviour
    main()

