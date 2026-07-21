"""Offline, versioned intent/tag contract and latency gates.

The authored fixture contains only bounded event labels. It verifies that the
normalizer and ranker preserve an explicit intent/tag contract; it is not
human-rated evidence of literary or semantic relevance. It is intentionally
separate from terminal content so relevance work cannot become prompt retrieval.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import random
import statistics
import time
from pathlib import Path
from typing import Callable

from bookshelf.data.quotes import QUOTES, Quote
from bookshelf.skill.quote_picker import (
    COMPACT_MAX_BYTES,
    INTENT_TAGS,
    normalize_event,
    select_quote_index,
)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "relevance-v1.json"
SELECTION_P95_RELEASE_MAX_MS = 30.0
Selector = Callable[[list[Quote], dict[str, int], list[int], list[str] | None], int]


def _legacy_quote_score(
    quote: Quote,
    index: int,
    shown_counts: dict[str, int],
    recent_set: set[int],
    context_tags: list[str] | None,
) -> float:
    """The score used by the pre-relevance Bookshelf selector (f2ef759)."""
    score = 0.0
    if context_tags:
        score += len(set(quote.tags) & set(context_tags))
    if index in recent_set:
        score -= 5.0
    return score - shown_counts.get(str(index), 0) * 0.5


def legacy_select_quote_index(
    quotes: list[Quote],
    shown_counts: dict[str, int],
    recent_indices: list[int],
    context_tags: list[str] | None = None,
    *,
    rng: random.Random,
) -> int:
    """Frozen implementation of the previously shipped novelty-first selector.

    This is a faithful, local copy of the selector released in commit f2ef759.
    The only change is accepting an RNG so the historical random tie-break is
    reproducible in an offline gate.
    """
    recent_set = set(recent_indices)
    unseen = [index for index in range(len(quotes)) if shown_counts.get(str(index), 0) == 0]
    candidates = [index for index in unseen if index not in recent_set]
    if not candidates:
        candidates = unseen
    if not candidates:
        candidates = [index for index in range(len(quotes)) if index not in recent_set]
    if not candidates:
        candidates = list(range(len(quotes)))

    scored = [
        (_legacy_quote_score(quotes[index], index, shown_counts, recent_set, context_tags), index)
        for index in candidates
    ]
    scored.sort(key=lambda result: result[0], reverse=True)
    top_score = scored[0][0]
    top_tier = [result for result in scored if result[0] >= top_score - 1.0]
    return rng.choice(top_tier)[1]


def _compact(quote: Quote) -> bool:
    return len(f"“{quote.text}” — {quote.author}, {quote.book_title}".encode("utf-8")) <= COMPACT_MAX_BYTES


def _fixture_cases(fixture_path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    cases = fixture.get("cases")
    if not isinstance(cases, list) or len(cases) < 160:
        raise ValueError("relevance fixture must contain at least 160 labeled normalized events")
    if len({case.get("id") for case in cases if isinstance(case, dict)}) != len(cases):
        raise ValueError("relevance fixture case IDs must be unique")
    if not all(isinstance(case, dict) for case in cases):
        raise ValueError("relevance fixture cases must be objects")
    return fixture, cases


def _tags_for(intents: list[str]) -> list[str]:
    return [tag for intent in intents for tag in INTENT_TAGS[intent]]


def _match_count(quote: Quote, tags: list[str]) -> int:
    return len(set(quote.tags).intersection(tags))


def _rng_for(case_id: str) -> random.Random:
    seed = int.from_bytes(hashlib.sha256(case_id.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def _selected(catalog: list[Quote], selector: Selector, tags: list[str]) -> Quote:
    index = selector(catalog, {}, [], tags)
    if not isinstance(index, int) or not 0 <= index < len(catalog):
        raise ValueError("selector returned an invalid quote index")
    return catalog[index]


def run_evaluation(
    fixture_path: Path = FIXTURE_PATH,
    *,
    selector: Selector = select_quote_index,
) -> dict[str, object]:
    """Score the shipped catalog against the authored intent/tag contract."""
    fixture, cases = _fixture_cases(fixture_path)
    catalog = list(QUOTES)
    if not catalog:
        raise ValueError("Bookshelf catalog is empty")

    total_positive = 0
    current_correct = 0
    legacy_correct = 0
    wrong_context = 0
    neutral_total = 0
    neutral_correct = 0
    per_intent: dict[str, dict[str, float]] = defaultdict(lambda: {"current": 0.0, "legacy": 0.0, "events": 0.0})

    for case in cases:
        metadata = case.get("metadata")
        expected_intents = case.get("expected_intents")
        if not isinstance(metadata, dict) or not all(isinstance(value, str) for value in metadata.values()):
            raise ValueError("fixture metadata must contain safe string labels only")
        if not isinstance(expected_intents, list) or not all(intent in INTENT_TAGS for intent in expected_intents):
            raise ValueError("fixture expected_intents must use known normalized intents")
        normalized = normalize_event(metadata)
        if normalized != expected_intents:
            raise ValueError(f"normalization drift in fixture case {case.get('id')!r}: {normalized!r}")

        tags = _tags_for(normalized)
        selected = _selected(catalog, selector, tags)
        kind = case.get("kind")
        if kind in {"neutral", "adversarial"}:
            neutral_total += 1
            neutral_correct += int(normalized == ["neutral"] and _compact(selected))
            continue
        if kind != "positive":
            raise ValueError("fixture cases must be positive, neutral, or adversarial")

        minimum = case.get("minimum_tag_matches")
        if not isinstance(minimum, int) or minimum < 1:
            raise ValueError("positive fixture cases need a positive minimum_tag_matches")
        legacy_index = legacy_select_quote_index(catalog, {}, [], tags, rng=_rng_for(str(case["id"])))
        legacy_quote = catalog[legacy_index]
        selected_matches = _match_count(selected, tags)
        legacy_matches = _match_count(legacy_quote, tags)
        is_correct = selected_matches >= minimum
        legacy_is_correct = legacy_matches >= minimum
        total_positive += 1
        current_correct += int(is_correct)
        legacy_correct += int(legacy_is_correct)
        wrong_context += int(selected_matches == 0)
        intent = normalized[0]
        per_intent[intent]["events"] += 1
        per_intent[intent]["current"] += int(is_correct)
        per_intent[intent]["legacy"] += int(legacy_is_correct)

    if not total_positive or not neutral_total:
        raise ValueError("fixture must include both positive and neutral/adversarial events")
    formatted_per_intent = {
        intent: {
            "p_at_1": 100.0 * values["current"] / values["events"],
            "legacy_p_at_1": 100.0 * values["legacy"] / values["events"],
            "events": values["events"],
        }
        for intent, values in sorted(per_intent.items())
    }
    p95 = benchmark_p95_ms(selector)
    return {
        "fixture_version": fixture["version"],
        "events": len(cases),
        "positive_events": total_positive,
        "catalog_quotes": len(catalog),
        "catalog_books": len({(quote.author, quote.book_title) for quote in catalog}),
        "relevance_p_at_1": 100.0 * current_correct / total_positive,
        "legacy_relevance_p_at_1": 100.0 * legacy_correct / total_positive,
        "relevance_gain_points": 100.0 * (current_correct - legacy_correct) / total_positive,
        "wrong_context_p_at_1": 100.0 * wrong_context / total_positive,
        "neutral_correctness": 100.0 * neutral_correct / neutral_total,
        "per_intent": formatted_per_intent,
        "selection_p95_ms_10000": p95,
    }


def benchmark_p95_ms(selector: Selector = select_quote_index) -> float:
    """Measure warm selection over 10,000 entries derived from shipped quotes.

    The raw value is reported for local comparisons. The release ceiling is a
    coarse linear-time regression guard with headroom for shared CI runners,
    not a promise of identical wall-clock latency on every machine.
    """
    catalog = (list(QUOTES) * ((10_000 + len(QUOTES) - 1) // len(QUOTES)))[:10_000]
    for _ in range(3):
        selector(catalog, {}, [], ["focus"])
    samples: list[float] = []
    for _ in range(25):
        start = time.perf_counter()
        selector(catalog, {}, [], ["focus"])
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.quantiles(samples, n=20, method="inclusive")[18]


def main() -> int:
    print(json.dumps(run_evaluation(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
