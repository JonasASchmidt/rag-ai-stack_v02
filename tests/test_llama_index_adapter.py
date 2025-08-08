import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

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
    monkeypatch.setattr(adapter, "MockLLM", DummyLLM)
    monkeypatch.setenv("EMBED_DIM", "16")
    monkeypatch.setattr(
        adapter, "Ollama", lambda *a, **k: DummyOllama(*a, **k, **ollama_kwargs)
    )


class DummyLLM:
    pass


def test_falls_back_when_ollama_missing(monkeypatch):
    monkeypatch.setattr(adapter, "PromptHelper", DummyPromptHelper)
    monkeypatch.setattr(adapter, "Settings", DummySettings)
    monkeypatch.setattr(adapter, "MockLLM", DummyLLM)
    monkeypatch.setattr(adapter, "Ollama", None)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, DummyLLM)


def test_falls_back_when_server_unreachable(monkeypatch):
    _setup_env(monkeypatch, fail=True)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, DummyLLM)


def test_success_sets_llm(monkeypatch):
    _setup_env(monkeypatch)
    adapter._configure_settings_from_env()
    assert isinstance(adapter.Settings.llm, DummyOllama)


def test_autostart_attempt(monkeypatch):
    started = {"called": False}

    _setup_env(monkeypatch, fail=True)
    monkeypatch.setenv("OLLAMA_AUTO_START", "1")
    monkeypatch.setattr(
        adapter.subprocess, "Popen", lambda *a, **k: started.__setitem__("called", True)
    )
    monkeypatch.setattr(adapter.time, "sleep", lambda _: None)

    adapter._configure_settings_from_env()
    assert started["called"]
    assert isinstance(adapter.Settings.llm, DummyLLM)


def test_passes_ollama_options(monkeypatch):
    captured = {}

    class CaptureOllama(DummyOllama):
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(adapter, "PromptHelper", DummyPromptHelper)
    monkeypatch.setattr(adapter, "Settings", DummySettings)
    monkeypatch.setattr(adapter, "Ollama", CaptureOllama)
    monkeypatch.setenv("EMBED_DIM", "16")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "2m")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "1024")
    monkeypatch.setenv("OLLAMA_NUM_BATCH", "8")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "128")

    adapter._configure_settings_from_env()

    assert captured["keep_alive"] == "2m"
    opts = captured["additional_kwargs"]
    assert opts["num_ctx"] == 1024
    assert opts["num_batch"] == 8
    assert opts["num_predict"] == 128
