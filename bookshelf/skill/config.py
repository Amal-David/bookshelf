"""Configuration for the ambient quote hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bookshelf.platform import app_data_dir, atomic_write_json

# State lives in a durable location, not /tmp/
APP_DIR_NAME = "bookshelf"

# Defaults (overridden by user config)
DEFAULT_CADENCE = 5
DEFAULT_CODEX_CADENCE = 5
DEFAULT_CONTEXT_MATCHING = True
DEFAULT_AMBIENT_CADENCE = 5


def _state_dir() -> Path:
    """Platform-aware state directory (same as bookshelf storage)."""
    return app_data_dir(APP_DIR_NAME)


HOOK_STATE_FILE = _state_dir() / "hook_state.json"


def load_hook_state() -> dict:
    """Load hook state (call counter, shown history, etc.)."""
    try:
        return json.loads(HOOK_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"call_count": 0, "last_quote_idx": -1, "shown_counts": {}, "recent_indices": []}


def save_hook_state(state: dict) -> None:
    """Save hook state."""
    try:
        atomic_write_json(HOOK_STATE_FILE, state, indent=None)
    except OSError:
        pass


def get_cadence() -> int:
    """Get the configured quote cadence (every Nth tool call)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("quote_cadence", DEFAULT_CADENCE)
    except Exception:
        return DEFAULT_CADENCE


def is_context_matching_enabled() -> bool:
    """Check if context matching is enabled."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("context_matching", DEFAULT_CONTEXT_MATCHING)
    except Exception:
        return DEFAULT_CONTEXT_MATCHING


def get_codex_cadence() -> int:
    """Get the configured Codex quote cadence (every Nth turn-ended event)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bookshelf.storage import load_config
        config = load_config()
        return config.get("codex_quote_cadence", DEFAULT_CODEX_CADENCE)
    except Exception:
        return DEFAULT_CODEX_CADENCE


def is_ambient_enabled() -> bool:
    """Return whether installed host adapters should emit ambient quotes."""
    try:
        from bookshelf.storage import load_config

        return bool(load_config().get("ambient_enabled", False))
    except Exception:
        return False


def get_ambient_cadence(host: str) -> int:
    """Return a safe positive cadence for a native host adapter."""
    try:
        from bookshelf.storage import load_config

        config = load_config()
        fallback_key = "codex_quote_cadence" if host == "codex" else "quote_cadence"
        value = config.get(
            "ambient_cadence",
            config.get(fallback_key, DEFAULT_AMBIENT_CADENCE),
        )
        return max(1, int(value))
    except (TypeError, ValueError, OSError):
        return DEFAULT_AMBIENT_CADENCE


def get_ambient_intent() -> str:
    """Return the user's explicit local theme for context-free Stop hooks."""
    try:
        from bookshelf.skill.quote_picker import ALLOWED_INTENTS
        from bookshelf.storage import load_config

        value = str(load_config().get("ambient_intent", "neutral")).casefold().strip()
        return value if value in ALLOWED_INTENTS else "neutral"
    except (TypeError, ValueError, OSError):
        return "neutral"
