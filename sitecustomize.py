"""Runtime patches for third-party compatibility issues."""

import sys
import types

# Stub chainlit.telemetry to prevent premature import of chainlit.config
if "chainlit.telemetry" not in sys.modules:
    stub = types.ModuleType("chainlit.telemetry")
    stub.trace_event = lambda *args, **kwargs: None
    sys.modules["chainlit.telemetry"] = stub


def _patch_chainlit() -> None:
    """Rebuild chainlit dataclasses to avoid Pydantic forward-ref errors."""
    try:
        # Import Action first so it's defined before config loads
        import chainlit.action  # noqa: F401
        import chainlit.config as config
        from pydantic.dataclasses import rebuild_dataclass

        rebuild_dataclass(config.CodeSettings)
    except Exception:
        # Silently ignore; patch only required on affected environments
        pass


_patch_chainlit()
