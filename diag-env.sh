#!/usr/bin/env bash
set -e

echo "=== SHELL INFO ==="
echo "Shell PID: $$"
echo "Shell executable:"; ps -p $$

echo
echo "=== ALIASES & TYPES ==="
alias | head -n 50
echo
echo "type python:"; type python || true
echo "type python3:"; type python3 || true
echo "type pip:"; type pip || true

echo
echo "=== PATH & WHICH ==="
echo "PATH=$PATH"
which -a python || true
which -a python3 || true
which -a pip || true

echo
echo "=== pyenv ==="
pyenv versions || true
pyenv which python || true
pyenv which python3 || true

echo
echo "=== Python env vars ==="
env | grep -E 'PYENV|PYTHON|VIRTUAL' || echo "-> none set"

echo
echo "=== Current Python info ==="
python --version || true
python -c 'import sys; print(sys.executable); print(sys.path)' || true

echo
echo "=== venv dir snapshot (if exists) ==="
if [ -d .venv ]; then
  ls -ld .venv .venv/bin .venv/lib* || true
else
  echo "No .venv directory"
fi
