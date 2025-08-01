# rag-ai-stack_v02

Simple but modular and extensible RAG AI stack to enable local document chat.

## Ziele

- Lokal mit eigenen Dokumenten chatten (RAG)
- Reproduzierbares, isoliertes Python-Setup
- Saubere Trennung zwischen Runtime- und Dev-Dependencies
- Isolierte Toolinstallationen mit `pyenv`, `venv`, `poetry` und `pipx`

## Voraussetzungen

- macOS / Unix-ähnlich
- Homebrew (optional, für `pyenv` und `pipx`)
- Git
- Kein globales `python`-Alias, das `pyenv` oder venv überschreibt

## Setup (einmalig pro Maschine / Projekt)

1. **Bootstrap ausführen**
   ```bash
   # im Projektverzeichnis
   chmod +x bootstrap.sh
   ./bootstrap.sh
