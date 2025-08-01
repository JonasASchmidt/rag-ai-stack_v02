import json
import sys
from pathlib import Path

from pypdf import PdfWriter

sys.path.append(str(Path(__file__).resolve().parents[1]))
from indexer.ingest import build_index


def test_build_index_handles_pdf_and_skips_binary(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    index_dir = tmp_path / "index"

    # text file
    (docs_dir / "a.txt").write_text("hello", encoding="utf-8")

    # pdf file
    pdf_path = docs_dir / "b.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as fh:
        writer.write(fh)

    # binary file
    (docs_dir / "c.bin").write_bytes(b"\x00\x01\x02")

    build_index(docs_dir, index_dir)
    data = json.loads((index_dir / "index.json").read_text(encoding="utf-8"))

    assert data["a.txt"] == "hello"
    assert "b.pdf" in data
    assert "c.bin" not in data
