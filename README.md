# rag-ai-stack\_v02

Modularer, lokaler RAG-AI-Stack zum Chatten mit eigenen Dokumenten.
Ziel dieses Repositories: ein **stabiler, reproduzierbarer Python-Setup** trotz pyenv/venv/Shim-Fallstricken.

## Kernideen

* **Fallback-Python**: Nutze ein unabhängiges, sauberes `python3` (z. B. vom python.org Installer) — keine Shim-Verwirrung.
* **Robustes venv**: Erstelle das virtuelle Environment ohne `ensurepip`-Edge-Cases, bootstrappe `pip` manuell.
* **Dependency-Management**: Nutze `poetry` (installiert im venv) für saubere, deklarative Abhängigkeiten.
* **Einfacher Entwickler-Workflow** über `Makefile`: `bootstrap`, `format`, `test`.
* **CI garantiert Konsistenz**: GitHub Actions validiert den gleichen Flow automatisch.

## Voraussetzungen (Host)

* macOS oder vergleichbares Unix
* Python 3.13.x (idealerweise installiert über python.org, nicht abhängig von kaputten pyenv-Shims)
* Git
* Homebrew (für einfache Installation von Tools, optional)

## Setup / Entwicklung (lokal)

```bash
# 1. Bootstrap (erstellt venv, installiert pip, poetry & deps)
make bootstrap

# 2. Formatierung prüfen
make format

# 3. Tests ausführen
make test
```

## Was passiert unter der Haube in `make bootstrap`

* echtes `python3` wird verwendet (pyenv-Shims werden temporär umgangen)
* neues `.venv` ohne `ensurepip` erzeugt
* `pip` via `get-pip.py` gebootstrapped
* `pip`, `setuptools`, `wheel`, `poetry` installiert
* Projektabhängigkeiten via `poetry install --no-root` installiert

## Snapshot / Reproducibility

```bash
pip freeze > requirements.txt
```

Damit hast du einen flachen Snapshot der aktuell installierten Pakete als Fallback.

## Optional: pyenv-Flow (nur wenn du versionierte Pythons brauchst)

```bash
pyenv install 3.13.5
pyenv local 3.13.5
pyenv rehash

rm -rf .venv
~/.pyenv/versions/3.13.5/bin/python -m venv --copies .venv
source .venv/bin/activate
python -m ensurepip --upgrade || true
python -m pip install --upgrade pip setuptools wheel poetry
poetry install --no-root
```

> Hinweis: Wenn `ensurepip` mit pyenv wieder bricht, bleib beim stabilen fallback-Flow mit dem system/python.org-Python.

## Git / Commit

Empfohlener erster Commit:

```bash
git add pyproject.toml poetry.lock README.md .gitignore setup-fallback.sh Makefile requirements.txt .github/workflows/ci.yml
git commit -m "Initial stable Python.org fallback setup with Makefile and CI"
git push origin main
```

## CI

Die GitHub Actions in `.github/workflows/ci.yml` führt bei jedem Push / PR:

1. `make bootstrap`
2. `make format` (macht Build rot bei Formatfehlern)
3. `make test` (macht Build rot bei fehlgeschlagenen Tests)

## Erweiterungen (nächste sinnvolle Schritte)

* Echte Tests schreiben im `tests/`-Verzeichnis
* Pre-commit-Hooks integrieren (`black`, `isort`, etc.)
* Release-/Version-Tagging
* Devcontainer oder Shell-Wrapper für Konsistenz auf anderen Maschinen

## Troubleshooting

* **`make bootstrap` bricht:** prüfe `python3`-Pfad (`pyenv shell system`), lösche `.venv` manuell und wiederhole.
* **`poetry` fehlt:** wird im venv installiert; falls du sie global brauchst, installiere sie über `pipx` außerhalb des venv.
* **Tests fehlen:** Lege eine Datei `tests/test_smoke.py` mit `assert True` an, damit `make test` initial grün läuft.
