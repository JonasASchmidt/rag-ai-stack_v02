# RAG AI Stack v0.2

This repository provides a small but complete retrieval augmented
generation (RAG) stack. Documents placed in ``DOCS_DIR`` are ingested into
an on‑disk vector store. A Chainlit based backend exposes a chat interface
which retrieves relevant nodes from the store and lets the LLM generate an
answer.

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

## Quick start

The stack can be launched with Docker containers:

```bash
# copy and adjust the configuration
cp .env.example .env

# build and start the indexer plus chat backend
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

# start the chat UI
chainlit run backend/app.py
```

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

