import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import chainlit as cl
from chainlit import ChatSettings
from chainlit.input_widget import Switch

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
    await ChatSettings(
        inputs=[Switch(id="internet_access", label="Internet access", initial=False)]
    ).send()
    cl.user_session.set("internet_access", False)
    await cl.Message(content="Index geladen. Stelle deine Frage!").send()


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    """Store updated chat settings in the user session."""
    cl.user_session.set("internet_access", settings.get("internet_access", False))


def internet_search(query: str) -> str:
    """Retrieve an answer from the internet using DuckDuckGo's instant API."""
    url = (
        "https://api.duckduckgo.com/?q="
        + urllib.parse.quote(query)
        + "&format=json&no_html=1&skip_disambig=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
        return data.get("AbstractText") or "Keine Online-Antwort gefunden."
    except Exception:
        return "Fehler beim Abrufen der Online-Informationen."


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming user messages."""
    if cl.user_session.get("internet_access", False):
        answer = internet_search(message.content)
    else:
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

    # ``AskActionMessage`` may return different structures depending on the
    # Chainlit version (e.g. an object with a ``value`` attribute or a plain
    # ``dict``).  Access the selected value in a version‑agnostic way to avoid
    # ``AttributeError`` when the result is a dictionary.
    value = None
    if result:
        if isinstance(result, dict):
            value = result.get("value")
        else:
            value = getattr(result, "value", None)

    if value == "down":
        detail = await cl.AskUserMessage(content="Bitte beschreibe das Problem.").send()

        # ``AskUserMessage`` can also return either an object with a
        # ``content`` attribute or a plain ``dict``.  Extract the text in a
        # flexible way so feedback logging works across Chainlit versions.
        detail_content = ""
        if detail:
            if isinstance(detail, dict):
                detail_content = detail.get("content", "")
            else:
                detail_content = getattr(detail, "content", "")

        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()}\t{message.content}\t{detail_content}\n"
            )
