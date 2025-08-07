"""Chainlit application providing a simple RAG chat interface."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import chainlit as cl
import chainlit.server as cls
import requests
from chainlit.config import config
from chainlit.input_widget import Switch
from dotenv import load_dotenv
from fastapi import Query
from llama_index.core.schema import NodeWithScore, TextNode

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adapters.llama_index.llama_index_adapter import (  # noqa: E402
    LlamaIndexIndexer,
    LlamaIndexResponseGenerator,
    LlamaIndexRetriever,
)

FEEDBACK_PATH = Path(__file__).with_name("feedback.log")


def internet_search(query: str) -> str:
    """Return a short snippet from an internet search."""

    try:  # pragma: no cover - network call
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json"},
            timeout=10,
        )
        if resp.ok:
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


@cl.on_chat_start
async def on_chat_start() -> None:
    load_dotenv()
    if _load_index():
        await cl.Message(content="Index geladen. Stelle deine Frage!").send()
    else:
        await cl.Message(
            content="Kein Index gefunden. Bitte führe zuerst den Indexer aus."
        ).send()

    files = await cl.AskFileMessage(
        content="Lade optionale Dateien hoch.",
        accept=["text/plain"],
        max_size_mb=20,
        max_files=3,
    ).send()
    uploaded: List[NodeWithScore] = []
    for f in files or []:
        text = f.content.decode("utf-8", errors="ignore")
        uploaded.append(
            NodeWithScore(
                node=TextNode(text=text, metadata={"file_name": f.name}),
                score=1.0,
            )
        )
    cl.user_session.set("uploaded_nodes", uploaded)

    settings = await cl.ChatSettings(
        [Switch(id="internet", label="Internet Search", initial=False)]
    ).send()
    cl.user_session.set("internet", settings.get("internet", False))


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("internet", settings.get("internet", False))


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if not retriever or not generator:
        await cl.Message(content="Kein Index geladen.").send()
        return
    cl.user_session.set("last_user_message", message.content)

    try:
        nodes: List[NodeWithScore] = list(retriever.retrieve(message.content))
        nodes.extend(cl.user_session.get("uploaded_nodes") or [])

        if cl.user_session.get("internet"):
            snippet = internet_search(message.content)
            if snippet:
                nodes.append(
                    NodeWithScore(
                        node=TextNode(text=snippet, metadata={"source": "Internet"}),
                        score=0.2,
                    )
                )

        answer = generator.generate(message.content, nodes)
    except Exception:
        logger.exception("Error during retrieval/generation")
        await cl.Message(
            content="Bei der Verarbeitung ist ein Fehler aufgetreten."
        ).send()
        return

    sources = ", ".join(
        sorted(
            {
                (getattr(getattr(n, "node", n), "metadata", {}) or {}).get("file_name")
                or (getattr(getattr(n, "node", n), "metadata", {}) or {}).get(
                    "source", ""
                )
                for n in nodes
                if getattr(getattr(n, "node", n), "metadata", None)
            }
        )
    )

    if sources:
        answer = f"{answer}\n\nQuellen: {sources}"

    sent = cl.Message(content="", stream=True)
    await sent.send()
    for token in answer.split():
        await sent.stream_token(token + " ")
    actions = [
        cl.Action(name="copy", value=answer, label="Copy"),
        cl.Action(name="retry", value=message.content, label="Retry"),
        cl.Action(name="vote", value="up", label="👍"),
        cl.Action(name="vote", value="down", label="👎"),
    ]
    await sent.update(actions=actions)


@cl.action_callback("retry")
async def retry_callback(action: cl.Action) -> None:
    last = cl.user_session.get("last_user_message")
    if last:
        await on_message(cl.Message(content=last))


@cl.action_callback("vote")
async def vote_callback(action: cl.Action) -> None:
    if action.value == "down":
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
