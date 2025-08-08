"""Chainlit application providing a simple RAG chat interface."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import chainlit as cl
import chainlit.server as cls
import httpx
from chainlit.config import config
from chainlit.input_widget import Switch
from dotenv import load_dotenv
from fastapi import Query
from llama_index.core import Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.schema import NodeWithScore, TextNode

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adapters.llama_index.llama_index_adapter import (  # noqa: E402
    LlamaIndexIndexer,
    LlamaIndexResponseGenerator,
    LlamaIndexRetriever,
    _configure_settings_from_env,
)

FEEDBACK_PATH = Path(__file__).with_name("feedback.log")


async def internet_search(query: str) -> str:
    """Return a short snippet from an internet search."""

    try:  # pragma: no cover - network call
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json"},
                timeout=10,
            )
            if resp.is_success:
                data = resp.json()
                return data.get("AbstractText") or ""
    except Exception:
        pass
    return ""


index = None
retriever: LlamaIndexRetriever | None = None
generator: LlamaIndexResponseGenerator | None = None


logger = logging.getLogger(__name__)


@cl.on_app_startup
def add_translation_alias() -> None:
    @cls.router.get("/_chainlit/project/translations", include_in_schema=False)
    async def legacy_project_translations(
        language: str = Query(default="de-DE", description="Language code")
    ) -> dict:
        """Serve translation strings for legacy frontend paths."""
        translation = config.load_translation(language)
        return {"translation": translation}


def _load_index() -> bool:
    """Load the persisted index and initialise helper objects.

    Returns ``True`` if the index was loaded successfully, otherwise ``False``.
    """

    global index, retriever, generator

    index_dir = Path(os.environ.get("INDEX_DIR", "vectorstore/llama"))
    if not index_dir.exists():
        return False

    try:
        index = LlamaIndexIndexer.load(index_dir)
    except Exception:
        return False

    retriever = LlamaIndexRetriever(index)
    generator = LlamaIndexResponseGenerator(index)
    return True


def _ingest_elements(elements: List[cl.Element]) -> None:
    """Persist uploaded elements and rebuild the index."""
    docs_dir = Path(os.environ.get("DOCS_DIR", "docs"))
    index_dir = Path(os.environ.get("INDEX_DIR", "vectorstore/llama"))
    docs_dir.mkdir(parents=True, exist_ok=True)
    for el in elements:
        if not getattr(el, "path", None):
            continue
        dest = docs_dir / (el.name or Path(el.path).name)
        dest.write_bytes(Path(el.path).read_bytes())
    indexer = LlamaIndexIndexer()
    global index, retriever, generator
    index = indexer.build(docs_dir, index_dir)
    retriever = LlamaIndexRetriever(index)
    generator = LlamaIndexResponseGenerator(index)


@cl.on_chat_start
async def on_chat_start() -> None:
    load_dotenv()
    _configure_settings_from_env()

    if _load_index():
        await cl.Message(content="Index geladen. Stelle deine Frage!").send()
    else:
        await cl.Message(
            content="Kein Index gefunden. Bitte führe zuerst den Indexer aus."
        ).send()

    if isinstance(Settings.llm, MockLLM):
        base_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        model = os.environ.get("LLM_MODEL", "llama3.1:latest")
        await cl.Message(
            content=(
                f"Ollama-Server unter {base_url} nicht erreichbar. "
                "Nutze MockLLM mit eingeschränkten Antworten. "
                f"Starte Ollama z. B. mit `ollama serve` und lade das Modell `ollama pull {model}` "
                "um echte Antworten zu erhalten."
            )
        ).send()

    settings = await cl.ChatSettings(
        [Switch(id="internet", label="Internet Search", initial=False)]
    ).send()
    cl.user_session.set("internet", settings.get("internet", False))


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("internet", settings.get("internet", False))


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if message.elements:
        _ingest_elements(message.elements)
    if not retriever or not generator:
        await cl.Message(content="Kein Index geladen.").send()
        return
    cl.user_session.set("last_user_message", message.content)

    try:
        nodes = await asyncio.to_thread(retriever.retrieve, message.content)
        nodes = list(nodes)

        if cl.user_session.get("internet"):
            snippet = await internet_search(message.content)
            if snippet:
                nodes.append(
                    NodeWithScore(
                        node=TextNode(text=snippet, metadata={"source": "Internet"}),
                        score=0.2,
                    )
                )
        answer_parts: list[str] = []
        sent = cl.Message(content="")
        await sent.send()

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def consume() -> None:
            while True:
                token = await queue.get()
                if token is None:
                    break
                answer_parts.append(token)
                await sent.stream_token(token)

        consumer = asyncio.create_task(consume())
        loop = asyncio.get_running_loop()

        if hasattr(generator, "agenerate_stream"):

            async def produce_async() -> None:
                async for token in generator.agenerate_stream(message.content, nodes):
                    await queue.put(token)
                await queue.put(None)

            producer = asyncio.create_task(produce_async())
        else:

            def produce_sync() -> None:
                for token in generator.generate_stream(message.content, nodes):
                    loop.call_soon_threadsafe(queue.put_nowait, token)
                loop.call_soon_threadsafe(queue.put_nowait, None)

            producer = asyncio.to_thread(produce_sync)

        await asyncio.gather(producer, consumer)

        answer = "".join(answer_parts)
        sources = ", ".join(
            sorted(
                {
                    (getattr(getattr(n, "node", n), "metadata", {}) or {}).get(
                        "file_name"
                    )
                    or (getattr(getattr(n, "node", n), "metadata", {}) or {}).get(
                        "source",
                        "",
                    )
                    for n in nodes
                    if getattr(getattr(n, "node", n), "metadata", None)
                }
            )
        )

        if sources:
            sources_text = f"\n\nQuellen: {sources}"
            answer += sources_text
            await sent.stream_token(sources_text)

        actions = [
            cl.Action(name="copy", payload={"answer": answer}, label="Copy"),
            cl.Action(name="retry", payload={}, label="Retry"),
            cl.Action(name="vote", payload={"direction": "up"}, label="👍"),
            cl.Action(name="vote", payload={"direction": "down"}, label="👎"),
        ]
        await sent.update(actions=actions)
    except Exception:
        logger.exception("Error during retrieval/generation")
        await cl.Message(
            content="Bei der Verarbeitung ist ein Fehler aufgetreten."
        ).send()
        return


@cl.action_callback("retry")
async def retry_callback(action: cl.Action) -> None:
    last = cl.user_session.get("last_user_message")
    if last:
        await on_message(cl.Message(content=last))


@cl.action_callback("vote")
async def vote_callback(action: cl.Action) -> None:
    if (action.payload or {}).get("direction") == "down":
        detail = await cl.AskUserMessage(content="Bitte beschreibe das Problem.").send()
        detail_content = (
            detail.get("content", "")
            if isinstance(detail, dict)
            else getattr(detail, "content", "")
        )
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()}\t{cl.user_session.get('last_user_message')}\t{detail_content}\n"
            )
