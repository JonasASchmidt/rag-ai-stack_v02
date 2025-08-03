# RAG AI Stack v0.2

This repository provides a small but complete retrieval augmented
generation (RAG) stack.  Documents placed in ``DOCS_DIR`` are ingested into
an on‑disk vector store.  A Chainlit based backend exposes a chat interface
which retrieves relevant nodes from the store and lets the LLM generate an
answer.

## Quick start

```bash
# copy and adjust the configuration
cp .env.example .env

# start the indexer and the chat backend
docker compose up --build
```

Put your documents into the volume mounted at ``docs/`` (or whatever
``DOCS_DIR`` points to).  The indexer watches this directory and rebuilds
the vector store whenever files change.  The Chainlit UI is available at
<http://localhost:8000>.

## Configuration

All runtime parameters are controlled via environment variables.  The most
important ones are shown below (see ``.env.example`` for the full list):

| Variable | Description |
|----------|-------------|
| ``DOCS_DIR`` | Directory containing the source documents |
| ``INDEX_DIR`` | Where the persistent vector store is written |
| ``LLM_MODEL`` / ``OLLAMA_API_URL`` | Model and endpoint used by the LlamaIndex ``Ollama`` LLM |
| ``CHUNK_SIZE`` / ``CHUNK_OVERLAP`` | Document chunking parameters |
| ``RETRIEVAL_K`` / ``FETCH_K`` | Retrieval depth controls |
| ``RESPONSE_MODE`` / ``THINKING_STEPS`` / ``TEMPERATURE`` | Response generation knobs |

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
architecture.  All interaction with ``llama_index`` happens inside
``core.adapters.llama_index``.  The rest of the code relies solely on the
abstract interfaces found in ``core.interfaces`` making it easy to swap out
implementations in the future.

