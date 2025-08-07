# RAG AI Stack v0.2

This repository provides a small but complete retrieval augmented
generation (RAG) stack. Documents placed in a folder are ingested into
an on‑disk vector store. In a chat interface, users can ask an LLM questions and it then retrieves information from the provided documents and generates answers, based on that.

## Repository layout

* ``core/`` – framework‑agnostic interfaces plus the concrete
  ``llama_index`` adapters used by the stack.
* ``indexer/`` – ingestion code and a file watcher that rebuilds the
  vector store whenever documents change.
* ``backend/`` – Chainlit application loading the persisted index and
  serving the chat UI.
* ``evaluator/`` – helper script for comparing answers against expected
  results.
* ``docs/`` – sample documents that can be indexed.
* ``tests/`` – small pytest suite.

## Requirements

Use Python 3.11 or 3.12. Python 3.13 is currently not supported by
Chainlit and will raise a pydantic dataclass error when starting the app.

## Quick start

The stack can be launched with Docker containers:

```bash
# copy and adjust the configuration
cp .env.example .env

# build and start the indexer, Ollama LLM and chat backend
docker compose up --build
```

Put your documents into the volume mounted at ``docs/`` (or whatever
``DOCS_DIR`` points to). The indexer watches this directory and rebuilds
the vector store whenever files change. The Chainlit UI is available at
<http://localhost:8000>.

### Running without Docker

The components can also be executed directly for local development:

```bash
# create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install indexer and backend dependencies
pip install -r indexer/requirements.txt -r backend/requirements.txt

# copy and adjust the configuration
cp .env.example .env

# build the index once
python -m indexer.ingest
# alternatively keep it up to date
# python -m indexer.watcher

# start the chat UI (use ``python -m`` so runtime patches are applied)
python -m chainlit run backend/app.py
```

The ``docker-compose.yml`` file starts an
[Ollama](https://ollama.ai) service that the other components connect to via
``OLLAMA_API_URL=http://ollama:11434``. For local development without Docker,
run your own Ollama server on ``http://localhost:11434`` instead and adjust
``OLLAMA_API_URL`` accordingly. Make sure the ``llama3.1:latest`` model is
available in your Ollama instance or change ``LLM_MODEL`` to another local
model.

## Configuration

All runtime parameters are controlled via environment variables. Start by
copying the sample file and adjusting it to your needs:

```bash
cp .env.example .env
```

The most important options are shown below (see ``.env.example`` for the full
list):

| Variable | Description |
|----------|-------------|
| ``DOCS_DIR`` | Directory containing the source documents |
| ``INDEX_DIR`` | Where the persistent vector store is written |
| ``LLM_MODEL`` / ``OLLAMA_API_URL`` | Model and endpoint used by the LlamaIndex ``Ollama`` LLM |
| ``LLM_REQUEST_TIMEOUT`` | Seconds to wait for the LlamaIndex ``Ollama`` LLM |
| ``OLLAMA_KEEP_ALIVE`` / ``OLLAMA_NUM_CTX`` / ``OLLAMA_NUM_BATCH`` / ``OLLAMA_NUM_PREDICT`` | Advanced Ollama runtime options |
| ``CHUNK_SIZE`` / ``CHUNK_OVERLAP`` | Document chunking parameters |
| ``EMBED_DIM`` | Size of the lightweight hashing embedding vector |
| ``RETRIEVAL_K`` / ``FETCH_K`` | Retrieval depth controls |
| ``MAX_INPUT_SIZE`` / ``NUM_OUTPUT`` | Prompt and output token limits |
| ``RESPONSE_MODE`` / ``THINKING_STEPS`` / ``TEMPERATURE`` | Response generation knobs |
| ``DEBOUNCE_SECONDS`` | Delay before the indexer reacts to file changes |

Tweak these values to trade off speed, precision and creativity.

## Evaluating the pipeline

The ``evaluator`` package contains a small script that can be used to
compare answers from the running backend with expected results:

```bash
python evaluator/eval.py --tests evaluator/tests.json
```

The script writes ``results.json`` with similarity scores based on
``difflib.SequenceMatcher``.

## Development

The project deliberately keeps dependencies minimal and uses a clean
architecture. All interaction with ``llama_index`` happens inside
``core.adapters.llama_index``. The rest of the code relies solely on the
abstract interfaces found in ``core.interfaces`` making it easy to swap out
implementations in the future.

### Local setup

Use the provided ``makefile`` for common tasks:

```bash
make bootstrap   # create virtual environment and install dependencies
make test        # run the pytest suite
make format      # check code style with black
```

## Helper scripts

Several utility scripts live in the project root:

* ``diag-env.sh`` – prints information about the current shell and Python
  environment to help with debugging.
* ``repair.sh`` – recreates the local ``.venv`` and reinstalls dependencies
  using Poetry.
* ``setup-fallback.sh`` – lightweight bootstrap in case the regular setup
  fails.

Run them with ``bash <script-name>`` when needed.

