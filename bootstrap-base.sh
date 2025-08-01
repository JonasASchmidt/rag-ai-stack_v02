#!/usr/bin/env bash
set -euo pipefail

echo "== Clean shell config (keine aliases, pyenv init laden) =="
source ~/.zprofile
source ~/.zshrc

echo "== Optional: Homebrew-Python entfernen =="
brew uninstall --ignore-dependencies python@3.13 || true
brew cleanup || true

echo "== Prüfe python.org-Python =="
which python3
python3 --version

echo "== Richte pyenv ein (optional) =="
if command -v pyenv >/dev/null 2>&1; then
  pyenv install -s 3.13.5
  pyenv rehash
  echo "pyenv versions:"
  pyenv versions
else
  echo "pyenv nicht installiert, überspringe."
fi

echo "== pipx & poetry =="
brew install pipx
pipx ensurepath
# lade neu, falls nötig
source ~/.zshrc
pipx install poetry

echo "== Status =="
which python3; python3 --version
which python || true
which poetry; poetry --version
