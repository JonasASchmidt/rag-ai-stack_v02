import pytest
import sys
from pathlib import Path

llama_index = pytest.importorskip("llama_index")
pytest.importorskip("llama_index.llms.ollama")

sys.path.append(str(Path(__file__).resolve().parents[1]))
from indexer.ingest import build_index


def test_build_index_runs(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.txt").write_text("hello", encoding="utf-8")
    index_dir = tmp_path / "index"

    build_index(docs_dir, index_dir)
    assert index_dir.exists()
