"""Fail-safe ambient quote delivery shared by native host adapters."""

from __future__ import annotations

from bookshelf.skill.config import (
    get_ambient_cadence,
    is_ambient_enabled,
    load_hook_state,
    save_hook_state,
)
from bookshelf.skill.quote_picker import (
    format_quote_message,
    pick_quote,
    total_quote_count,
)

_COUNTER_KEYS = {
    "claude": "claude_turn_count",
    "codex": "codex_turn_count",
    "hermes": "hermes_turn_count",
    "pi": "pi_turn_count",
}


def ambient_quote(
    host: str,
    *,
    context_tags: list[str] | None = None,
) -> dict | None:
    """Return a quote when the opt-in cadence is due, otherwise ``None``.

    Adapter failures are deliberately swallowed: a companion feature must never
    be able to break an agent turn.
    """
    try:
        if not is_ambient_enabled():
            return None

        normalized_host = host.lower().strip()
        counter_key = _COUNTER_KEYS.get(
            normalized_host,
            f"{normalized_host or 'unknown'}_turn_count",
        )
        state = load_hook_state()
        turn_count = int(state.get(counter_key, 0)) + 1
        state[counter_key] = turn_count
        save_hook_state(state)

        cadence = get_ambient_cadence(normalized_host)
        if turn_count % cadence != 0:
            return None
        return pick_quote(context_tags)
    except Exception:
        return None


def ambient_message(
    host: str,
    *,
    context_tags: list[str] | None = None,
) -> str | None:
    """Return the native-adapter message when the cadence is due."""
    quote = ambient_quote(host, context_tags=context_tags)
    if not quote:
        return None
    try:
        return format_quote_message(quote, total_quote_count())
    except Exception:
        return None
