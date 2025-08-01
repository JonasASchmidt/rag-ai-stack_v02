#!/usr/bin/env bash
set -euo pipefail

echo "== fallback venv setup =="

# 0. Ensure we try to bypass pyenv shims but don’t fail if pyenv isn't present
if command -v pyenv >/dev/null 2>&1; then
  pyenv shell system || true
fi

# 1. Clean previous venv
echo "Cleaning old venv..."
deactivate 2>/dev/null || true
rm -rf .venv

# 2. Create venv without pip to avoid ensurepip edge cases
echo "Creating venv without pip..."
python3 -m venv .venv --without-pip
source .venv/bin/activate

# 3. Bootstrap pip
echo "Bootstrapping pip..."
if ! command -v python >/dev/null 2>&1; then
  echo "Error: python not in PATH after activating venv."
  exit 1
fi

curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python /tmp/get-pip.py --force-reinstall

# 4. Upgrade core tooling separately to reduce failure surface
echo "Upgrading core tooling..."
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools
python -m pip install --upgrade wheel

# 5. Ensure poetry is available
if ! command -v poetry >/dev/null 2>&1; then
  echo "Warning: poetry not found. Installing via pipx (requires pipx to be available)."
  if ! command -v pipx >/dev/null 2>&1; then
    echo "pipx missing — installing pipx via pip (user install)..."
    python -m pip install --user pipx
    export PATH="$HOME/.local/bin:$PATH"
    pipx ensurepath || true
  fi
  pipx install poetry
fi

# 6. Install project dependencies
echo "Installing project dependencies with poetry..."
poetry install --no-root

# 7. Snapshot requirements
echo "Generating requirements.txt..."
python -m pip freeze > requirements.txt

# 8. Summary
echo "Done. Activate with: source .venv/bin/activate"
which python
python --version
which pip
pip --version
which poetry || echo "poetry not found in PATH"
poetry --version 2>/dev/null || echo "poetry version unavailable"
