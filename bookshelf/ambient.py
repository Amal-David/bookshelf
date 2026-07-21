"""Fail-safe ambient quote delivery shared by native host adapters."""

from __future__ import annotations

from bookshelf.skill.config import (
    get_ambient_cadence,
    get_ambient_intent,
    is_ambient_enabled,
)
from bookshelf.skill.quote_picker import (
    INTENT_TAGS,
    format_ambient_quote_message,
    pick_quote,
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
        from bookshelf.skill.quote_state import QuoteStateStore

        store = QuoteStateStore()
        # A state recovery must be acknowledged by an interactive command.
        # Ambient adapters never announce it or resume delivery on their own.
        if store.recovery_notice_pending():
            return None
        turn_count = store.increment_counter(counter_key)

        cadence = get_ambient_cadence(normalized_host)
        if turn_count % cadence != 0:
            return None
        selected_tags = list(context_tags or ())
        if not selected_tags:
            selected_tags.extend(INTENT_TAGS[get_ambient_intent()])
        return pick_quote(selected_tags, ambient_only=True)
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
        return format_ambient_quote_message(quote)
    except Exception:
        return None
