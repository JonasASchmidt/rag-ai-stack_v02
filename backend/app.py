import json
from datetime import datetime
from pathlib import Path

import chainlit as cl

INDEX_PATH = Path(__file__).parent / "index.json"
FEEDBACK_PATH = Path(__file__).parent / "feedback.log"


def load_index() -> dict:
    if INDEX_PATH.exists():
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def retrieve(query: str, data: dict) -> str:
    docs = data.get("documents", [])
    query_lower = query.lower()
    for doc in docs:
        if query_lower in doc.lower():
            return doc
    return "Keine passende Antwort gefunden."


index = {}


@cl.on_chat_start
async def on_chat_start() -> None:
    """Load the retrieval index when the chat session starts."""
    global index
    index = load_index()
    await cl.Message(content="Index geladen. Stelle deine Frage!").send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming user messages."""
    answer = retrieve(message.content, index)
    sent = cl.Message(content=answer)
    await sent.send()

    actions = [
        cl.Action(name="feedback", value="up", label="👍"),
        cl.Action(name="feedback", value="down", label="👎"),
    ]
    result = await cl.AskActionMessage(
        content="War die Antwort hilfreich?",
        actions=actions,
    ).send()

    if result and result.value == "down":
        detail = await cl.AskUserMessage(content="Bitte beschreibe das Problem.").send()
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()}\t{message.content}\t{detail.content}\n"
            )
