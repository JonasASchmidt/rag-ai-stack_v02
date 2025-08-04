# Local RAG AI Chat App

Develop a self‑contained retrieval‑augmented generation (RAG) app that can ingest many heterogenous documents (pdf, md, txt, doc, images, xls) from a directory (folder docs sotred in a variable named DOCS_DIR), and builds an on‑disk vector store from the extracted information, and exposes a chat interface (like ChatGPT, using Chainlit or OPenWebUI or a comparable solution) that retrieves relevant nodes and lets an LLM generate answers. For example when the docs folder contains food recipes, I want to be able to chat with th LM and let it give me whole recipes, assit and guide me while cooking and ask it questions which it will anser correctly, from the ingested document information. It must never lie (hallucinate) or make things up. The app must never send data from the vector store or the ingested docs to a LLM in the cloud, so no other person or LLm can know the provide source data.

This concept outlines the full implementation path for a modular, configurable RAG application ready for both local experimentation and scalable deployment.


## General Development & Documentation Guidelines

Always act like an experienced software architect and senior developer, that knows her ways around best practices and latest technologies and make sure to create modular, sustainable and reliable and scalable architecture and code solutions.

Regularly check the app (and complete repo) for integrity and get rid of stale/unused code, dependencies, libraries or any other assets.

Always document code with smart comments. Also document the app architecture and functionality and how to set it up and how to operate it  (installation, index creation, evaluation, testing, what to do after pull and how to run and use it) in the README.md.

Also document what helper scripts (like: diag-env.sh, repair.sh, setup-fallback.sh) do if they are still needed.



## Advanced Concept & Planned Architecture


### Core Abstractions

Define clean interfaces (Indexer, Retriever, ResponseGenerator, Evaluator) to keep application code agnostic of specific libraries, enabling future swapping of implementations.

Provide LlamaIndex-based adapters implementing these interfaces, with configuration drawn from environment variables for chunking, retrieval depth, and LLM parameters so it can be fine grained controlled what the data in the vector store looks like and when and how much the LLM "thinks" while retrieving information and generating answers.


## Document Ingestion & Vector Store

The indexer builds or updates a VectorStoreIndex from Markdown, text, PDF, doc, xls or OCR’d image files and persists it to a folder (stord in variable INDEX_DIR) for the backend to load at startup.

A watchdog-based file watcher monitors DOCS_DIR and debounces changes before re‑running ingestion, ensuring the vector store stays current.


## Chat Backend & Frontend

The chat frontend app initializes retriever and response generator from the persisted index, serves a chat UI, and streams answers, while also showing an activity indicator (e.g.: animated ring around the stop button that appears instead of the send-message button, when the user sent a message to the AI), for debuggin purpoeses along with source file names that the chunks the answer was generated from, stem from. Users can provide thumbs‑up/down feedback, negative feedback is logged with a timestamp and query for later review. The feedback must not be mandatory. 

Every answer must provide the following functions/buttons on the top and bottom edge: copy, retry, vote (thumbsup/-down).

The text input field must provide a button to attach files (which then can be questioned in the current chat session, togehter with the vector store) and an option to activate internet saerch (which must be deactivated by default).


## Configuration & Environment

All runtime behavior—paths, model endpoints, chunk sizes, retrieval depth, temperature, debounce delay—is controlled via environment variables so deployments can tune performance and creativity without code changes.


## Evaluation & Testing

An evaluator script sends prompts to the running backend, compares answers to expected results with (e.g. with difflib.SequenceMatcher), and writes similarity scores to results.json, enabling regression checks or automated quality scoring.

A lightweight pytest suite ensures components remain stable, and a Makefile streamlines common dev tasks.


## Planned Extensions

### Scalability
Optionally containerize components for distributed deployment, add caching for repeated queries, and support alternative vector stores or LLM backends.

### User Experience
Enable multi-language support, conversational memory, and richer feedback analytics.

### Operational Concerns
Integrate structured logging, metrics, and health checks; enforce authentication/authorization for production; provide CLI utilities for batch operations.


