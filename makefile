.PHONY: bootstrap test test-fast format format-fix clean

VENV := .venv
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null)
POETRY_INSTALL_ARGS ?= --with llama

bootstrap:
	@echo "== bootstrap =="
	@if command -v pyenv >/dev/null && [ -n "$(PYTHON_VERSION)" ]; then \
		pyenv shell $(PYTHON_VERSION) >/dev/null 2>&1 || true; \
	fi
	@rm -rf $(VENV)
	@python3 -m venv $(VENV) --without-pip
	@. $(VENV)/bin/activate && \
		curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
		python /tmp/get-pip.py --force-reinstall && \
                python -m pip install --upgrade pip setuptools wheel poetry && \
                PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 poetry install --no-root $(POETRY_INSTALL_ARGS)

test:
	@echo "== test =="
	@. $(VENV)/bin/activate && poetry run pytest -q

test-fast:
	@echo "== test-fast =="
	@. $(VENV)/bin/activate && poetry run pytest -m "not slow" -q

format:
	@echo "== format check =="
	@. $(VENV)/bin/activate && poetry run black --check .

format-fix:
	@echo "== format fix =="
	@. $(VENV)/bin/activate && poetry run black .

clean:
	@echo "== clean =="
	@rm -rf $(VENV)
