import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

llama_index = pytest.importorskip("llama_index")
from llama_index.llms.ollama import Ollama as RealOllama

sys.path.append(str(Path(__file__).resolve().parents[1]))
from indexer.ingest import build_index  # noqa: E402


class DummyClient:
    def list(self):
        return {"models": []}


class DummyOllama(RealOllama):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = DummyClient()


def test_build_index_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.adapters.llama_index.llama_index_adapter.Ollama", DummyOllama
    )

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.txt").write_text("hello", encoding="utf-8")
    index_dir = tmp_path / "index"

    build_index(docs_dir, index_dir)
    assert index_dir.exists()
