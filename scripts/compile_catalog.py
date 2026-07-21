#!/usr/bin/env python3
"""Compile and verify the provenance-aware Bookshelf v2 catalog.

The compiler is deliberately offline.  It accepts a reviewed staging directory
only when materialising a new catalog; normal ``--check`` verification uses the
shipped JSON and generated manifests, so releases do not depend on a network
or on a private source checkout.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = ROOT / "bookshelf" / "data"
DOCS = ROOT / "docs"
CATALOG_PATH = DATA / "catalog_v2.json"
MANIFEST_PATH = DATA / "catalog_manifest.json"
SOURCE_MANIFEST_PATH = DATA / "catalog_source_manifest.json"
REJECTION_REPORT_PATH = DATA / "catalog_rejection_report.json"
COUNTS_DOC_PATH = DOCS / "catalog-counts.md"

ALLOWED_RIGHTS = {"public-domain-us", "cc0", "permissive-attribution"}
BIDI_CONTROL_CODEPOINTS = {
    "\u061c",  # Arabic letter mark
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u202a",  # left-to-right embedding
    "\u202b",  # right-to-left embedding
    "\u202c",  # pop directional formatting
    "\u202d",  # left-to-right override
    "\u202e",  # right-to-left override
    "\u2066",  # left-to-right isolate
    "\u2067",  # right-to-left isolate
    "\u2068",  # first strong isolate
    "\u2069",  # pop directional isolate
}
REQUIRED_QUOTE_FIELDS = {
    "quote_id",
    "work_id",
    "text",
    "author",
    "book_title",
    "source_identifier",
    "source_url",
    "locator",
    "rights_class",
    "rights_jurisdiction_note",
    "verification_state",
    "verification_method",
    "admission_state",
    "verified_at",
    "digest_sha256",
    "source_repository_url",
    "extraction_snapshot_sha256",
}


def canonical(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"\w+", normalized, flags=re.UNICODE))


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def has_unsafe_control(text: str) -> bool:
    return any(
        unicodedata.category(char) == "Cc" or char in BIDI_CONTROL_CODEPOINTS
        for char in text
    )


def token_set(text: str) -> set[str]:
    return set(canonical(text).split())


def near_duplicate(left: str, right: str) -> bool:
    """Conservative offline near-duplicate gate used for imported records."""
    left_tokens, right_tokens = token_set(left), token_set(right)
    if not left_tokens or not right_tokens:
        return True
    smaller, larger = sorted((left_tokens, right_tokens), key=len)
    containment = len(smaller) >= 12 and smaller.issubset(larger)
    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    ratio = difflib.SequenceMatcher(None, canonical(left), canonical(right)).ratio()
    if min(len(left_tokens), len(right_tokens)) < 12:
        return containment or (ratio >= 0.94 and overlap >= 0.94)
    return containment or (ratio >= 0.90 and overlap >= 0.86)


def _near_duplicate_from_parts(
    left_normalized: str,
    left_tokens: set[str],
    right_normalized: str,
    right_tokens: set[str],
    shared_tokens: int,
) -> bool:
    """Apply ``near_duplicate`` without repeating normalization or set work."""
    if not left_tokens or not right_tokens:
        return True
    smaller = min(len(left_tokens), len(right_tokens))
    union = len(left_tokens) + len(right_tokens) - shared_tokens
    containment = smaller >= 12 and shared_tokens == smaller
    overlap = shared_tokens / union
    if containment:
        return True
    if smaller < 12:
        return overlap >= 0.94 and difflib.SequenceMatcher(
            None, left_normalized, right_normalized
        ).ratio() >= 0.94
    return overlap >= 0.86 and difflib.SequenceMatcher(
        None, left_normalized, right_normalized
    ).ratio() >= 0.90


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _source_summary(title: str, author: str) -> str:
    """A transparent source note, not an invented editorial synopsis."""
    return (
        f"This catalog record identifies the Standard Ebooks reading edition of {title} by {author}. "
        "It was added through Bookshelf's provenance-reviewed public-domain expansion, using only "
        "reading XHTML from the edition source and retaining a direct source identifier, locator, "
        "snapshot digest, verification date, and U.S.-specific rights note for every linked quote. "
        "This is intentionally a source note rather than an editorial synopsis: the reviewed import "
        "bundle establishes text provenance and reuse conditions, but does not supply a verified "
        "critical summary of the work. Readers should use the linked primary-source edition to assess "
        "context, translation, and punctuation. Standard Ebooks dedicates its edition work to CC0 and "
        "describes the underlying text as public domain in the United States; that is not a claim of "
        "clearance in every jurisdiction. Bookshelf keeps this record distinct from its legacy editorial "
        "catalog so the provenance boundary remains visible during browsing and corrections. It also gives "
        "future contributors a precise, reviewable starting point for replacing this note with an editorial "
        "summary supported by a separately cited source rather than inferred from a title or isolated passage."
    )


def _build_books(quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_work: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for quote in quotes:
        by_work[quote["work_id"]].append(quote)
    books: list[dict[str, Any]] = []
    for work_id, entries in sorted(by_work.items(), key=lambda item: (item[1][0]["book_title"].casefold(), item[1][0]["author"].casefold())):
        first = entries[0]
        books.append(
            {
                "work_id": work_id,
                "title": first["book_title"],
                "author": first["author"],
                "year": 0,
                "genre": "fiction",
                "mood": ["late night reflection", "self-discovery"],
                "summary": _source_summary(first["book_title"], first["author"]),
                "summary_kind": "provenance-note",
                "source_identifier": first["source_identifier"],
                "source_url": first["source_url"],
                "rights_class": first["rights_class"],
                "rights_jurisdiction_note": first["rights_jurisdiction_note"],
                "verification_state": first["verification_state"],
                "verified_at": first["verified_at"],
                "digest_sha256": digest("\x1f".join((work_id, first["source_identifier"], first["source_url"]))),
            }
        )
    return books


def validate_new_records(quotes: list[dict[str, Any]], books: list[dict[str, Any]]) -> Counter[str]:
    """Raise on unsafe imports and return any rejection reasons for reporting."""
    reasons: Counter[str] = Counter()
    works = {book["work_id"] for book in books}
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    accepted_parts: list[tuple[str, set[str]]] = []
    token_index: dict[str, list[int]] = defaultdict(list)
    for quote in quotes:
        missing = REQUIRED_QUOTE_FIELDS - quote.keys()
        if missing:
            raise ValueError(f"missing required quote metadata: {sorted(missing)}")
        text = quote["text"]
        textual_fields = (
            text,
            quote["author"],
            quote["book_title"],
            quote["source_identifier"],
            quote["source_url"],
            quote["source_repository_url"],
            quote["locator"],
            quote["verification_method"],
        )
        if not all(isinstance(value, str) for value in textual_fields) or any(
            has_unsafe_control(value) for value in textual_fields
        ):
            raise ValueError(f"unsafe control character in {quote['quote_id']}")
        byte_length = len(text.encode("utf-8"))
        if not 60 <= byte_length <= 280:
            raise ValueError(f"unsafe quote length in {quote['quote_id']}: {byte_length}")
        if quote["rights_class"] not in ALLOWED_RIGHTS:
            raise ValueError(f"unsupported rights class in {quote['quote_id']}")
        source_identifier = quote["source_identifier"]
        if not re.fullmatch(r"standardebooks/[a-z0-9][a-z0-9._-]*", source_identifier):
            raise ValueError(f"opaque or non-primary source in {quote['quote_id']}")
        expected_repository_url = f"https://github.com/{source_identifier}"
        if (
            quote["source_url"] != expected_repository_url
            or quote["source_repository_url"] != expected_repository_url
        ):
            raise ValueError(f"mismatched source repository in {quote['quote_id']}")
        if not re.fullmatch(r"[0-9a-f]{64}", quote["extraction_snapshot_sha256"]):
            raise ValueError(f"invalid extraction snapshot digest in {quote['quote_id']}")
        if not quote["verification_method"].strip():
            raise ValueError(f"missing verification method in {quote['quote_id']}")
        if quote["work_id"] not in works:
            raise ValueError(f"unresolved work in {quote['quote_id']}")
        if quote["quote_id"] in seen_ids:
            raise ValueError(f"duplicate quote ID {quote['quote_id']}")
        if quote["digest_sha256"] != digest(text):
            raise ValueError(f"digest mismatch in {quote['quote_id']}")
        normalized = canonical(text)
        if normalized in seen_texts:
            raise ValueError(f"exact or near duplicate in {quote['quote_id']}")
        tokens = set(normalized.split())
        candidates: Counter[int] = Counter(
            index for token in tokens for index in token_index.get(token, ())
        )
        if any(
            _near_duplicate_from_parts(
                normalized,
                tokens,
                accepted_parts[index][0],
                accepted_parts[index][1],
                shared,
            )
            for index, shared in candidates.items()
        ):
            raise ValueError(f"exact or near duplicate in {quote['quote_id']}")
        seen_ids.add(quote["quote_id"])
        seen_texts.add(normalized)
        if quote["admission_state"] != "review-pending-human-review":
            raise ValueError(f"unexpected admission state in {quote['quote_id']}")
        if quote["verification_state"] != "source-linked-review-pending":
            raise ValueError(f"unexpected verification state in {quote['quote_id']}")
        accepted_parts.append((normalized, tokens))
        accepted_index = len(accepted_parts) - 1
        for token in tokens:
            token_index[token].append(accepted_index)
    return reasons


def validate_against_legacy(quotes: list[dict[str, Any]]) -> None:
    """Keep the import gate independent from the staging bundle's assertion."""
    legacy_texts = [record["text"] for record in _legacy_records()]
    legacy_exact = {canonical(text) for text in legacy_texts}
    legacy_parts = [(canonical(text), token_set(text)) for text in legacy_texts]
    inverted: dict[str, list[int]] = defaultdict(list)
    for index, (_, tokens) in enumerate(legacy_parts):
        for token in tokens:
            inverted[token].append(index)
    for quote in quotes:
        text = quote["text"]
        normalized = canonical(text)
        if normalized in legacy_exact:
            raise ValueError(f"exact duplicate of legacy quote in {quote['quote_id']}")
        tokens = set(normalized.split())
        overlaps: Counter[int] = Counter(
            index for token in tokens for index in inverted.get(token, ())
        )
        for index, shared in overlaps.items():
            older_normalized, older_tokens = legacy_parts[index]
            if _near_duplicate_from_parts(
                normalized,
                tokens,
                older_normalized,
                older_tokens,
                shared,
            ):
                raise ValueError(f"near duplicate of legacy quote in {quote['quote_id']}")


def _legacy_records() -> list[dict[str, Any]]:
    from bookshelf.data.quotes import LEGACY_QUOTES

    return [
        {
            "quote_id": f"legacy-{index}",
            "work_id": f"legacy-work-{index}",
            "text": quote.text,
            "author": quote.author,
            "book_title": quote.book_title,
            "verification_state": "legacy-unverified",
            "admission_state": "legacy",
            "rights_class": "legacy-unknown",
            "source_identifier": "legacy-catalog",
        }
        for index, quote in enumerate(LEGACY_QUOTES)
    ]


def build_manifest(catalog: dict[str, Any], rejection_reasons: Counter[str]) -> dict[str, Any]:
    new_quotes = catalog["quotes"]
    new_books = catalog["books"]
    legacy = _legacy_records()
    all_texts = [record["text"] for record in legacy] + [record["text"] for record in new_quotes]
    normalized = [canonical(text) for text in all_texts]
    duplicate_groups = len(normalized) - len(set(normalized))
    return {
        "schema_version": 2,
        "catalog_digest_sha256": digest(json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        "counts": {
            "quotes": len(all_texts),
            "unique_normalized_quotes": len(set(normalized)),
            "catalogued_books": _catalogued_book_count(),
            "quoted_works": len({(record["author"], record["book_title"]) for record in legacy + new_quotes}),
            "new_quotes": len(new_quotes),
            "new_books": len(new_books),
            "legacy_quotes": len(legacy),
            "legacy_catalogued_books": catalog["legacy_catalogued_books"],
            "legacy_normalized_duplicate_records": duplicate_groups,
        },
        "rights_class_counts": dict(sorted(Counter(record["rights_class"] for record in legacy + new_quotes).items())),
        "verification_state_counts": dict(sorted(Counter(record["verification_state"] for record in legacy + new_quotes).items())),
        "admission_state_counts": dict(sorted(Counter(record["admission_state"] for record in legacy + new_quotes).items())),
        "source_counts": dict(sorted(Counter(record["source_identifier"] for record in legacy + new_quotes).items())),
        "book_counts": dict(sorted(Counter(record["book_title"] for record in legacy + new_quotes).items())),
        "author_counts": dict(sorted(Counter(record["author"] for record in legacy + new_quotes).items())),
        "rejected_record_reason_counts": dict(sorted(rejection_reasons.items())),
    }


def _catalogued_book_count() -> int:
    from bookshelf.data.books import load_all_books

    return len(load_all_books())


def write_generated_artifacts(catalog: dict[str, Any], source_manifest: dict[str, Any], rejection_reasons: Counter[str]) -> None:
    manifest = build_manifest(catalog, rejection_reasons)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SOURCE_MANIFEST_PATH.write_text(json.dumps(source_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REJECTION_REPORT_PATH.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rejected_records": sum(rejection_reasons.values()),
                "reasons": dict(sorted(rejection_reasons.items())),
                "policy": "Reject opaque sources, unsupported rights, unresolved works, malformed control characters, unsafe length, digest mismatches, exact duplicates, and near duplicates.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    counts = manifest["counts"]
    COUNTS_DOC_PATH.parent.mkdir(exist_ok=True)
    COUNTS_DOC_PATH.write_text(
        "# Generated catalog counts\n\n"
        "This file is generated by `python3 scripts/compile_catalog.py --check`; do not edit it by hand.\n\n"
        f"- **{counts['quotes']:,} shipped quote records** ({counts['unique_normalized_quotes']:,} normalized unique texts)\n"
        f"- **{counts['catalogued_books']:,} catalogued books**\n"
        f"- **{counts['quoted_works']:,} works referenced by quotes**\n"
        f"- **{counts['new_quotes']:,} primary-source-linked v2 quotes, pending human review** from **{counts['new_books']:,} new works**\n"
        f"- **{counts['legacy_quotes']:,} legacy quote records**, explicitly marked `legacy-unverified`\n"
        f"- **{counts['legacy_normalized_duplicate_records']:,} legacy normalized duplicate records** retained for compatibility and reported separately\n\n"
        "See `bookshelf/data/catalog_manifest.json` for source, author, work, rights, verification, and rejection breakdowns.\n",
        encoding="utf-8",
    )


def import_staging(staging: Path) -> None:
    candidates = _read_jsonl(staging / "standard-curated" / "merged-candidates.jsonl")
    for candidate in candidates:
        # The staging bundle was fetched from moving repository branches. Keep
        # its exact excerpt/archive digest and locator, but do not present a
        # mutable source link as immutable provenance.
        candidate["verification_state"] = "source-linked-review-pending"
        candidate["verification_method"] = (
            "Fetched an unpinned Standard Ebooks source snapshot and retained "
            "the exact excerpt digest, archive digest, and XHTML locator; an "
            "immutable repository commit pin and human excerpt review remain pending."
        )
        candidate["source_repository_url"] = (
            f"https://github.com/{candidate['source_identifier']}"
        )
        candidate["source_url"] = candidate["source_repository_url"]
        candidate["extraction_snapshot_sha256"] = candidate.pop("source_archive_sha256")
        candidate.pop("source_archive_url", None)
        candidate["admission_state"] = "review-pending-human-review"
    books = _build_books(candidates)
    validate_new_records(candidates, books)
    validate_against_legacy(candidates)
    catalog = {
        "schema_version": 2,
        "legacy_catalogued_books": 983,
        "quotes": candidates,
        "books": books,
    }
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    source_manifest = _read_json(staging / "research-primary" / "standard_ebooks_primary_manifest_v1.json")
    source_manifest["release_boundary"] = (
        "The imported records retain source identifiers, repository links, "
        "XHTML locators, excerpt digests, and extraction-snapshot digests, but "
        "the staging sources were not pinned to immutable repository commits. "
        "Every v2 record therefore remains source-linked-review-pending and "
        "must not be described as source-verified."
    )
    source_manifest["extraction_contract"]["locator_strategy"] = (
        "Record the repository identifier, XHTML relative path and paragraph "
        "locator, normalized excerpt SHA-256, and extraction-snapshot SHA-256. "
        "Immutable commit pins were not captured for this release, so records "
        "remain review-pending."
    )
    write_generated_artifacts(catalog, source_manifest, Counter())


def check() -> None:
    catalog = _read_json(CATALOG_PATH)
    validate_new_records(catalog["quotes"], catalog["books"])
    validate_against_legacy(catalog["quotes"])
    expected = build_manifest(catalog, Counter())
    actual = _read_json(MANIFEST_PATH)
    if actual != expected:
        raise ValueError("catalog manifest drift; rerun the compiler")
    if not SOURCE_MANIFEST_PATH.is_file() or not REJECTION_REPORT_PATH.is_file() or not COUNTS_DOC_PATH.is_file():
        raise ValueError("generated catalog artifacts are missing")
    counts = actual["counts"]
    if counts["unique_normalized_quotes"] < 3100 or counts["catalogued_books"] < 1100:
        raise ValueError("catalog floor not met")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.staging_root:
        import_staging(args.staging_root)
    check()
    print(_read_json(MANIFEST_PATH)["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
