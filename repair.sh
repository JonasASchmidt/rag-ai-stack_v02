#!/usr/bin/env bash
set -euo pipefail

echo "== repair.sh: intelligentes venv-Setup =="

# Helpers
cmd_exists() { command -v "$1" >/dev/null 2>&1; }

# 1. Decide Python source
USE_PYENV=true
# if pyenv is present and current shim is active
if cmd_exists pyenv && [[ "$(which python3)" == *".pyenv/shims/"* ]]; then
  echo "pyenv shim detected: $(which python3)"
  echo "1) Use pyenv Python (preferred if venv creation works)"
  echo "2) Bypass shim for system/python.org Python"
  read -rp "Choose [1/2] (default 1): " choice
  choice=${choice:-1}
  if [[ "$choice" == "2" ]]; then
    echo "Temporarily bypassing pyenv shims"
    pyenv shell system 2>/dev/null || true
    USE_PYENV=false
  else
    echo "Using pyenv Python explicitly"
    # ensure version is set
    if [ -f .python-version ]; then
      PYVER=$(<.python-version)
    else
      echo "No .python-version; defaulting to 3.13.5"
      PYVER="3.13.5"
      pyenv local "$PYVER"
    fi
    if ! pyenv versions --bare | grep -qx "$PYVER"; then
      echo "Installing pyenv Python $PYVER..."
      pyenv install "$PYVER"
    fi
  fi
else
  echo "No active pyenv shim or pyenv not present; using system/python.org Python"
  USE_PYENV=false
fi

# 2. Determine python binary
if [ "$USE_PYENV" = true ]; then
  PYTHON_BIN="$(pyenv which python)"
else
  # pick the first python3 not from pyenv shims
  PYTHON_BIN=$(which -a python3 | grep -v ".pyenv/shims" | head -n1)
  if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: no non-pyenv python3 found in PATH"
    exit 1
  fi
fi
echo "Using interpreter: $PYTHON_BIN"

# 3. Recreate venv
echo "Recreating .venv"
deactivate 2>/dev/null || true
rm -rf .venv
if [ "$USE_PYENV" = true ]; then
  # use copies to avoid shim pitfalls
  "$PYTHON_BIN" -m venv --copies .venv
else
  "$PYTHON_BIN" -m venv .venv --without-pip || true
fi

# 4. Activate
# shellcheck source=/dev/null
source .venv/bin/activate

# 5. Bootstrap pip/setuptools/wheel
echo "Bootstrapping pip/setuptools/wheel"
if ! python -m pip --version >/dev/null 2>&1; then
  echo "pip missing; installing via get-pip.py"
  curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
  python /tmp/get-pip.py --force-reinstall
fi

# Upgrade core tools (do separately to reduce failure surface)
python -m pip install --upgrade pip || true
python -m pip install --upgrade setuptools || true
python -m pip install --upgrade wheel || true

# 6. Dependencies
if cmd_exists poetry; then
  echo "Installing project dependencies via poetry (no-root)"
  poetry install --no-root || echo "poetry install failed; continuing"
else
  echo "Warning: poetry not found in PATH. Skipping dependency install."
fi

# 7. Export requirements.txt as snapshot
echo "Generating requirements.txt"
pip freeze > requirements.txt

# 8. Summary
echo "== Done =="
echo "Python: $(which python) $(python --version 2>&1 | head -n1)"
echo "pip: $(pip --version 2>&1 | head -n1)"
echo "requirements.txt contains:"
head -n 20 requirements.txt
