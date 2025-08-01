# rag-ai-stack_v02

Lokaler RAG-Stack zum Chatten mit eigenen Dokumenten vibe-gecodet zusammen mit OPenAI's Codex und ChatGPT 04-mini und 04-mini-high.

## Voraussetzungen

* Python 3.13
* Git und `make`
* Ein Unix-artiges Betriebssystem (macOS, Linux, WSL)

## Setup

```bash
# virtuelle Umgebung und Abhängigkeiten
make bootstrap

# optional: Formatierung prüfen
make format

# Tests ausführen
make test
```

## Eigenen Dokumenten-Index bauen

Lege deine Texte in ein Verzeichnis wie `docs/` und generiere den JSON-Index,
den der Chat verwendet:

```bash
source .venv/bin/activate
DOCS_DIR=docs INDEX_DIR=backend poetry run python indexer/ingest.py
```

Der Index landet als `backend/index.json`.

## Chat lokal starten

```bash
source .venv/bin/activate
poetry run chainlit run backend/app.py
```

Nach dem Start ist die Oberfläche unter <http://localhost:8000> erreichbar.

## Nützliche Makefile-Ziele

* `make format-fix` – formatiert den Code
* `make clean` – entfernt die virtuelle Umgebung
