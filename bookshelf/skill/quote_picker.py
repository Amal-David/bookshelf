"""Private, deterministic relevance-ranked quote selection.

The ambient path accepts only a small normalized event fingerprint.  It never
uses command text, file names, prompts, or model output as retrieval input.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from bookshelf.skill.quote_state import QuoteStateStore

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RECENT_WINDOW = 50
COMPACT_MAX_BYTES = 360
AMBIENT_MAX_BYTES = 220
AMBIENT_MAX_WORDS = 32
ALLOWED_INTENTS = (
    "debug",
    "verify",
    "build",
    "ship",
    "review",
    "refactor",
    "collaborate",
    "recover",
    "neutral",
)

INTENT_TAGS = {
    "debug": ("perseverance", "resilience", "patience"),
    "verify": ("discipline", "focus", "perseverance"),
    "build": ("creativity", "ambition", "growth"),
    "ship": ("courage", "success", "ambition"),
    "review": ("wisdom", "growth", "relationships"),
    "refactor": ("simplicity", "discipline", "focus"),
    "collaborate": ("leadership", "relationships", "friendship"),
    "recover": ("resilience", "patience", "courage"),
    "neutral": (),
}

# These phrases are matched against a bounded *metadata label* only.  They are
# deliberately word-boundary expressions so e.g. ``relationship`` cannot mean
# ``ship`` and ``debugger`` cannot mean ``debug``.
_INTENT_PATTERNS = (
    ("debug", re.compile(r"\b(debug|bug|error|fix)\b", re.IGNORECASE)),
    ("verify", re.compile(r"\b(test|tests|verify|verification|assert)\b", re.IGNORECASE)),
    ("build", re.compile(r"\b(build|compile|package|create)\b", re.IGNORECASE)),
    ("ship", re.compile(r"\b(ship|deploy|release|publish|merge)\b", re.IGNORECASE)),
    ("review", re.compile(r"\b(review|comment|audit)\b", re.IGNORECASE)),
    ("refactor", re.compile(r"\b(refactor|simplify|cleanup|optimize)\b", re.IGNORECASE)),
    ("collaborate", re.compile(r"\b(collaborate|team|pair|handoff)\b", re.IGNORECASE)),
    ("recover", re.compile(r"\b(recover|rollback|retry|restore)\b", re.IGNORECASE)),
)
_CATALOG_METRICS: dict[
    tuple[int, int, int, int],
    list[tuple[str, str, int, bool, bool]],
] = {}
_BIDI_CONTROL_CODEPOINTS = frozenset(
    {0x061C, 0x200E, 0x200F}
    | set(range(0x202A, 0x202F))
    | set(range(0x2066, 0x206A))
)


def _canonical(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"\w+", value, flags=re.UNICODE))


@lru_cache(maxsize=32_768)
def _quote_id_from_values(author: str, book_title: str, text: str) -> str:
    payload = "\x1f".join((_canonical(author), _canonical(book_title), _canonical(text)))
    return "q_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def quote_id(quote: Any) -> str:
    """Stable content identity, unaffected by catalog position or order."""
    return getattr(quote, "quote_id", "") or _quote_id_from_values(
        quote.author, quote.book_title, quote.text
    )


@lru_cache(maxsize=16_384)
def _work_id_from_values(author: str, book_title: str) -> str:
    payload = "\x1f".join((_canonical(author), _canonical(book_title)))
    return "w_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def work_id(quote: Any) -> str:
    return getattr(quote, "work_id", "") or _work_id_from_values(
        quote.author, quote.book_title
    )


def _quote_metrics(quote: Any) -> tuple[str, str, int, bool, bool]:
    compact = _compact_payload(quote.text, quote.author, quote.book_title)
    ambient = _ambient_payload(quote.text, quote.author, quote.book_title)
    return (
        quote_id(quote),
        work_id(quote),
        len(_canonical(quote.text).split()),
        compact is not None,
        ambient is not None,
    )


def _has_control_characters(value: str) -> bool:
    """Reject terminal controls and directional overrides/isolate controls."""
    return any(
        unicodedata.category(character) == "Cc"
        or ord(character) in _BIDI_CONTROL_CODEPOINTS
        for character in value
    )


def _compact_payload(text: Any, author: Any, book: Any) -> str | None:
    """Return a safe compact payload, or ``None`` when catalog data is unsafe."""
    fields = (text, author, book)
    if not all(isinstance(field, str) and field and not _has_control_characters(field) for field in fields):
        return None
    payload = f"“{text}” — {author}, {book}"
    return payload if len(payload.encode("utf-8")) <= COMPACT_MAX_BYTES else None


def _ambient_payload(text: Any, author: Any, book: Any) -> str | None:
    """Return a compact payload that fits the stricter ambient turn budget."""
    payload = _compact_payload(text, author, book)
    if payload is None:
        return None
    if len(payload.encode("utf-8")) > AMBIENT_MAX_BYTES:
        return None
    if len(payload.split()) > AMBIENT_MAX_WORDS:
        return None
    return payload


def normalize_event(input_data: dict[str, Any] | None) -> list[str]:
    """Return up to four allow-listed intents from safe event metadata only."""
    if not isinstance(input_data, dict):
        return ["neutral"]
    explicit = input_data.get("intent")
    if isinstance(explicit, str) and explicit.casefold().strip() in ALLOWED_INTENTS:
        return [explicit.casefold().strip()]
    # Tool/event names are metadata labels, not user content.  Never inspect
    # command, path, prompt, transcript, response, repository, or arguments.
    labels = [input_data.get(key, "") for key in ("tool_name", "event", "event_name")]
    safe_label = " ".join(
        value[:160] for value in labels if isinstance(value, str) and value.isascii()
    )
    matches = [intent for intent, pattern in _INTENT_PATTERNS if pattern.search(safe_label)]
    return matches[:4] or ["neutral"]


def get_context_tags(input_data: dict) -> list[str]:
    """Compatibility wrapper returning tags for the privacy-safe intent profile."""
    return [tag for intent in normalize_event(input_data) for tag in INTENT_TAGS[intent]]


def total_quote_count() -> int:
    from bookshelf.data.quotes import QUOTES

    return len(QUOTES)


def format_quote_message(quote: dict, total_quotes: int | None = None) -> str:
    """Format the compact default payload; diagnostics are never implicit."""
    try:
        payload = _compact_payload(quote["text"], quote["author"], quote["book"])
    except (KeyError, TypeError):
        payload = None
    if payload is None:
        raise ValueError("quote is unsafe or exceeds compact delivery budget")
    return payload


def format_ambient_quote_message(quote: dict) -> str:
    """Format a safe quote for ambient insertion after an agent turn."""
    try:
        payload = _ambient_payload(quote["text"], quote["author"], quote["book"])
    except (KeyError, TypeError):
        payload = None
    if payload is None:
        raise ValueError("quote is unsafe or exceeds ambient delivery budget")
    return payload


def format_quote_details(quote: dict, total_quotes: int) -> str:
    """Explicit verbose output for terminals, never used by ambient adapters."""
    compact = format_quote_message(quote, total_quotes)
    tags = " ".join(f"#{tag}" for tag in quote.get("tags", [])[:3])
    return f"{compact}\n{tags}\n[{quote.get('unique_shown', 0)}/{total_quotes} unique quotes shown]"


def _is_compact(quote: Any) -> bool:
    return _quote_metrics(quote)[3]


def _metrics_for_catalog(quotes: list) -> list[tuple[str, str, int, bool, bool]]:
    """Cache immutable catalog-derived values; state is never cached here."""
    if not quotes:
        return []
    key = (id(quotes), len(quotes), id(quotes[0]), id(quotes[-1]))
    cached = _CATALOG_METRICS.get(key)
    if cached is None:
        cached = [_quote_metrics(item) for item in quotes]
        _CATALOG_METRICS.clear()
        _CATALOG_METRICS[key] = cached
    return cached


def select_quote_index(
    quotes: list,
    shown_counts: dict[str, int],
    recent_indices: list,
    context_tags: list[str] | None = None,
    *,
    feedback: dict[str, int] | None = None,
    ambient_only: bool = False,
) -> int:
    """Select deterministically: relevance, compactness, then variety signals."""
    if not quotes:
        raise ValueError("no compact quotes are available")
    feedback = feedback or {}
    target_tags = frozenset(context_tags or ())
    quote_metrics = _metrics_for_catalog(quotes)
    recent_positions: set[int] = set()
    recent_identifiers: set[str] = set()
    for value in recent_indices:
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            position = int(value)
            if 0 <= position < len(quotes):
                recent_positions.add(position)
        elif isinstance(value, str):
            recent_identifiers.add(value)
    recent_work_ids = {
        quote_metrics[position][1] for position in recent_positions
    }
    if recent_identifiers:
        # Build the stable-ID lookup only when SQLite history actually needs it.
        id_to_work = {metrics[0]: metrics[1] for metrics in quote_metrics}
        recent_work_ids.update(
            id_to_work[identifier]
            for identifier in recent_identifiers
            if identifier in id_to_work
        )

    best: tuple[tuple[int, int, int, int, int, int, int], str, int] | None = None
    has_counts = bool(shown_counts)
    feedback_get = feedback.get
    for index, quote in enumerate(quotes):
        identifier, quote_work_id, words, compact, ambient = quote_metrics[index]
        if not compact or (ambient_only and not ambient):
            continue
        matches = len(target_tags.intersection(quote.tags)) if target_tags else 0
        # A direct match is lexicographically above all novelty preferences.
        relevance = 1 if matches else 0
        count = (
            int(shown_counts.get(identifier, shown_counts.get(str(index), 0)))
            if has_counts
            else 0
        )
        is_recent = int(
            index in recent_positions or identifier in recent_identifiers
        )
        same_work = int(quote_work_id in recent_work_ids)
        key = (
            relevance,
            -is_recent,
            -count,
            matches,
            int(feedback_get(identifier, 0)),
            -same_work,
            -words,
        )
        if best is None or key > best[0] or (key == best[0] and identifier < best[1]):
            best = (key, identifier, index)
    if best is None:
        raise ValueError("no compact quotes are available")
    return best[2]


def _state_store() -> QuoteStateStore:
    return QuoteStateStore()


def pick_quote(
    context_tags: list[str] | None = None,
    *,
    ambient_only: bool = False,
) -> dict | None:
    """Pick and atomically record a compact quote using stable identities."""
    from bookshelf.data.quotes import QUOTES
    from bookshelf.skill.config import HOOK_STATE_FILE

    if not QUOTES:
        return None
    try:
        store = _state_store()
        store.migrate_legacy_indices((quote_id(item) for item in QUOTES), HOOK_STATE_FILE)
        index = -1

        def choose(
            shown_counts: dict[str, int],
            recent_ids: list[str],
            feedback: dict[str, int],
        ) -> str:
            nonlocal index
            index = select_quote_index(
                QUOTES,
                shown_counts,
                recent_ids,
                context_tags,
                feedback=feedback,
                ambient_only=ambient_only,
            )
            return quote_id(QUOTES[index])

        selected_id, shown, unique = store.select_and_record(choose)
        selected = QUOTES[index]
        return {
            "id": selected_id,
            "work_id": work_id(selected),
            "text": selected.text,
            "author": selected.author,
            "book": selected.book_title,
            "tags": list(selected.tags),
            "times_shown": shown,
            "unique_shown": unique,
        }
    except (OSError, ValueError, TypeError, sqlite3.Error):
        return None


def set_last_quote_feedback(helpful: bool) -> bool:
    """Persist one explicit vote for the last locally delivered quote."""
    try:
        store = _state_store()
        identifier = store.last_quote_id()
        if not identifier:
            return False
        store.set_feedback(identifier, helpful)
        return True
    except (OSError, sqlite3.Error):
        return False
