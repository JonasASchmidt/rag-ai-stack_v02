import pytest
from llama_index.core.llms.mock import MockLLM

from core.adapters.llama_index import llama_index_adapter as adapter


class DummyPromptHelper:
    def __init__(self, **kwargs):
        pass


class DummySettings:
    llm = None
    embed_model = None
    prompt_helper = None


class DummyClient:
    def __init__(self, fail=False):
        self.fail = fail

    def list(self):  # pragma: no cover - trivial
        if self.fail:
            raise OSError("boom")
        return {"models": []}


class DummyOllama:
    def __init__(self, *_, fail=False, **__):
        self.client = DummyClient(fail=fail)


def _setup_env(monkeypatch, **ollama_kwargs):
    monkeypatch.setattr(adapter, "PromptHelper", DummyPromptHelper)
    monkeypatch.setattr(adapter, "Settings", DummySettings)
    monkeypatch.setenv("EMBED_DIM", "16")
    monkeypatch.setattr(
        adapter, "Ollama", lambda *a, **k: DummyOllama(*a, **k, **ollama_kwargs)
    )


def test_falls_back_when_ollama_missing(monkeypatch):
    monkeypatch.setattr(adapter, "PromptHelper", DummyPromptHelper)
    monkeypatch.setattr(adapter, "Settings", DummySettings)
    monkeypatch.setattr(adapter, "Ollama", None)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, MockLLM)


def test_falls_back_when_server_unreachable(monkeypatch):
    _setup_env(monkeypatch, fail=True)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, MockLLM)


def test_success_sets_llm(monkeypatch):
    _setup_env(monkeypatch)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, DummyOllama)
