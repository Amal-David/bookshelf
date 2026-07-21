"""Read-only catalog metadata and provenance helpers."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).parent


def _canonical(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"\w+", value, flags=re.UNICODE))


def _stable_id(prefix: str, *values: str) -> str:
    payload = "\x1f".join(_canonical(value) for value in values)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


@lru_cache(maxsize=1)
def manifest() -> dict[str, Any]:
    return json.loads((_DATA_DIR / "catalog_manifest.json").read_text(encoding="utf-8"))


def counts() -> dict[str, int]:
    """Return the compiler-produced source of truth for public count surfaces."""
    return dict(manifest()["counts"])


def provenance_for(quote: Any) -> dict[str, str]:
    """Return an explicit provenance boundary for both legacy and v2 quotes."""
    quote_id = getattr(quote, "quote_id", "") or _stable_id(
        "legacy", quote.author, quote.book_title, quote.text
    )
    work_id = getattr(quote, "work_id", "") or _stable_id(
        "legacy-work", quote.author, quote.book_title
    )
    digest = getattr(quote, "digest_sha256", "") or hashlib.sha256(
        quote.text.encode("utf-8")
    ).hexdigest()
    return {
        "quote_id": quote_id,
        "work_id": work_id,
        "source_identifier": getattr(quote, "source_identifier", "") or "legacy-catalog",
        "source_url": getattr(quote, "source_url", ""),
        "source_locator": getattr(quote, "source_locator", ""),
        "rights_class": getattr(quote, "rights_class", "") or "legacy-unknown",
        "rights_jurisdiction_note": getattr(quote, "rights_jurisdiction_note", ""),
        "verification_state": getattr(quote, "verification_state", "") or "legacy-unverified",
        "admission_state": getattr(quote, "admission_state", "") or "legacy",
        "verified_at": getattr(quote, "verified_at", ""),
        "digest_sha256": digest,
    }
