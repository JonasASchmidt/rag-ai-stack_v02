"""Chainlit application providing a simple RAG chat interface."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adapters.llama_index.llama_index_adapter import (  # noqa: E402
    LlamaIndexIndexer,
    LlamaIndexResponseGenerator,
    LlamaIndexRetriever,
)

FEEDBACK_PATH = Path(__file__).with_name("feedback.log")


index = None
retriever: LlamaIndexRetriever | None = None
generator: LlamaIndexResponseGenerator | None = None


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


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if not retriever or not generator:
        await cl.Message(content="Kein Index geladen.").send()
        return

    nodes = retriever.retrieve(message.content)
    answer = generator.generate(message.content, nodes)

    sources = ", ".join(
        sorted(
            {
                n.metadata.get("file_name") or n.metadata.get("source", "")
                for n in nodes
                if getattr(n, "metadata", None)
            }
        )
    )

    if sources:
        answer = f"{answer}\n\nQuellen: {sources}"

    sent = cl.Message(content=answer)
    await sent.send()

    actions = [
        cl.Action(name="feedback", value="up", label="👍"),
        cl.Action(name="feedback", value="down", label="👎"),
    ]
    result = await cl.AskActionMessage(
        content="War die Antwort hilfreich?", actions=actions
    ).send()

    value = (
        result.get("value")
        if isinstance(result, dict)
        else getattr(result, "value", None)
    )
    if value == "down":
        detail = await cl.AskUserMessage(content="Bitte beschreibe das Problem.").send()
        detail_content = (
            detail.get("content", "")
            if isinstance(detail, dict)
            else getattr(detail, "content", "")
        )
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()}\t{message.content}\t{detail_content}\n"
            )
