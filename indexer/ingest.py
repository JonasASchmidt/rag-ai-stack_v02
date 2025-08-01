import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader

SUPPORTED_TEXT_EXTS = {".txt", ".md", ".json", ".rst"}


def _read_file(path: Path) -> str | None:
    """Return textual content for *path* or ``None`` if unsupported."""
    suffix = path.suffix.lower()
    try:
        if suffix in SUPPORTED_TEXT_EXTS:
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pragma: no cover - unexpected read errors
        logging.error("Failed to read %s: %s", path, exc)
        return None
    logging.info("Skipping unsupported file type: %s", path)
    return None


def build_index(docs_dir: Path, index_dir: Path) -> None:
    """Build or update a simple JSON index from documents."""
    index_dir.mkdir(parents=True, exist_ok=True)
    index_file = index_dir / "index.json"
    index = {}
    if index_file.exists():
        try:
            index = json.loads(index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logging.warning("Existing index is invalid JSON. Rebuilding.")
            index = {}

    updated_paths = set()
    for path in docs_dir.glob("**/*"):
        if not path.is_file():
            continue
        content = _read_file(path)
        if content is None:
            continue
        rel_path = str(path.relative_to(docs_dir))
        index[rel_path] = content
        updated_paths.add(rel_path)

    # Remove entries for files that no longer exist
    index = {k: v for k, v in index.items() if k in updated_paths}

    index_file.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logging.info("Indexed %d documents into %s", len(index), index_file)


def main() -> None:
    load_dotenv()
    docs_dir = Path(os.environ.get("DOCS_DIR", "docs"))
    index_dir = Path(os.environ.get("INDEX_DIR", "index"))
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logging.info("Starting ingestion from %s to %s", docs_dir, index_dir)
    build_index(docs_dir, index_dir)


if __name__ == "__main__":
    main()
