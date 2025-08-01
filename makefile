.PHONY: help bootstrap test format clean

VENV := .venv

help:
	@echo "Targets:"
	@echo "  make bootstrap  # setup venv, pip, poetry and install deps"
	@echo "  make test       # run tests"
	@echo "  make format     # check formatting"
	@echo "  make clean      # remove venv"

bootstrap:
	@echo "== bootstrap =="
	-@pyenv shell system 2>/dev/null || true
	@rm -rf $(VENV)
	@python3 -m venv $(VENV) --without-pip
	@. $(VENV)/bin/activate && \
		curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
		python /tmp/get-pip.py --force-reinstall && \
		python -m pip install --upgrade pip setuptools wheel poetry && \
		poetry install --no-root

test:
	@echo "== test =="
	@. $(VENV)/bin/activate && poetry run pytest -q || true

format:
	@echo "== format check =="
	@. $(VENV)/bin/activate && poetry run black --check .

clean:
	@echo "== clean =="
	@rm -rf $(VENV)
