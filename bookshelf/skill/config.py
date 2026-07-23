"""Configuration for the ambient quote hook."""

from __future__ import annotations

from pathlib import Path

from bookshelf.platform import app_data_dir

# State lives in a durable location, not /tmp/
APP_DIR_NAME = "bookshelf"

# Default (overridden by user config)
DEFAULT_AMBIENT_CADENCE = 5


def _state_dir() -> Path:
    """Platform-aware state directory (same as bookshelf storage)."""
    return app_data_dir(APP_DIR_NAME)


# Legacy hook_state.json path. No longer written; QuoteStateStore (SQLite) owns
# ambient state. Kept only as the one-time migration source for pre-upgrade
# installs — see quote_picker.pick_quote's migrate_legacy_indices call.
HOOK_STATE_FILE = _state_dir() / "hook_state.json"


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
