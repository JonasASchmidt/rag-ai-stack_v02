#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(pwd)"
PYTHON_VERSION="3.13.5"
ZSHRC="$HOME/.zshrc"

echo "==> Bootstrapping project in ${PROJECT_DIR}"

# 1. pyenv sicherstellen (via Homebrew)
if ! command -v pyenv >/dev/null; then
  echo "[1/9] Installing pyenv via Homebrew..."
  if ! command -v brew >/dev/null; then
    echo "ERROR: Homebrew nicht gefunden. Installiere Homebrew oder pyenv manuell." >&2
    exit 1
  fi
  brew install pyenv
else
  echo "[1/9] pyenv ist bereits installiert."
fi

# 2. pyenv-Initialisierung in Shell-Config sicherstellen
need_reload=false
if ! grep -Fxq 'export PYENV_ROOT="$HOME/.pyenv"' "$ZSHRC" 2>/dev/null; then
  echo "[2/9] Füge pyenv-Init zu $ZSHRC hinzu."
  {
    echo ''
    echo '# pyenv bootstrap (hinzugefügt von bootstrap.sh)'
    echo 'export PYENV_ROOT="$HOME/.pyenv"'
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
    echo 'eval "$(pyenv init --path)"'
    echo 'eval "$(pyenv init -)"'
  } >> "$ZSHRC"
  need_reload=true
else
  echo "[2/9] pyenv ist schon in $ZSHRC konfiguriert."
fi

if [ "$need_reload" = true ]; then
  echo "[3/9] Lade Shell-Konfiguration neu (source ~/.zshrc) oder mache es hier provisorisch."
  # Versuch, es für das Script zu sourcen (funktioniert nur, wenn kompatibel)
  # shellcheck source=/dev/null
  source "$ZSHRC" || true
else
  echo "[3/9] Keine erneute Shell-Ladung nötig."
fi

# 4. Gewünschtes Python via pyenv installieren
echo "[4/9] Stelle sicher, dass Python $PYTHON_VERSION via pyenv installiert ist..."
if ! pyenv versions --bare | grep -qx "$PYTHON_VERSION"; then
  pyenv install "$PYTHON_VERSION"
else
  echo "[4/9] Python $PYTHON_VERSION ist bereits installiert."
fi

# 5. Lokales Projekt-Python setzen
echo "[5/9] Setze lokale Python-Version auf $PYTHON_VERSION"
cd "$PROJECT_DIR"
pyenv local "$PYTHON_VERSION"

# 6. Virtuelles Environment neu erstellen
echo "[6/9] (Re)Erstelle .venv"
rm -rf .venv
python -m venv .venv

# 7. Aktivieren & Tooling aktualisieren
echo "[7/9] Aktiviere venv und upgrade pip/setuptools/wheel"
# Aktivieren für diesen Kontext
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# 8. Poetry via pipx isoliert installieren
echo "[8/9] Installiere poetry über pipx"
if ! command -v pipx >/dev/null; then
  if command -v brew >/dev/null; then
    echo "[8/9] pipx fehlt, installiere pipx..."
    brew install pipx
  else
    echo "WARNUNG: pipx nicht installiert und Homebrew fehlt; überspringe poetry." >&2
  fi
fi

if command -v pipx >/dev/null; then
  pipx ensurepath
  export PATH="$HOME/.local/bin:$PATH"  # sicherstellen für diese Session
  if ! pipx list | grep -q 'poetry'; then
    pipx install poetry
  else
    echo "[8/9] poetry ist bereits über pipx installiert."
  fi
fi

# 9. Projekt-Abhängigkeiten installieren (wenn vorhanden)
if [ -f pyproject.toml ]; then
  echo "[9/9] Installiere Projektabhängigkeiten mit poetry"
  poetry install
else
  echo "[9/9] Keine pyproject.toml gefunden; überspringe dependency install."
fi

echo "✅ Bootstrap abgeschlossen."
echo "Nächste Schritte:"
echo "  source .venv/bin/activate"
echo "  which python && python --version"
echo "  poetry --version"
