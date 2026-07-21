"""Stable identity, private migration, and contention coverage for quote state."""

from __future__ import annotations

import json
import multiprocessing
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bookshelf.data.quotes import Quote
from bookshelf.skill.quote_picker import (
    AMBIENT_MAX_BYTES,
    AMBIENT_MAX_WORDS,
    COMPACT_MAX_BYTES,
    RECENT_WINDOW,
    format_ambient_quote_message,
    format_quote_message,
    quote_id,
    select_quote_index,
)
from bookshelf.skill.quote_state import QuoteStateStore, StateRecoveryRequired


def _process_write(database: str, identifier: str, count: int) -> None:
    store = QuoteStateStore(Path(database))
    for _ in range(count):
        store.record_selection(identifier)


def _process_select_once(database: str, identifiers: list[str], results) -> None:
    store = QuoteStateStore(Path(database))

    def choose(counts: dict[str, int], recent: list[str], _feedback: dict[str, int]) -> str:
        return min(
            identifiers,
            key=lambda identifier: (
                identifier in recent,
                counts.get(identifier, 0),
                identifier,
            ),
        )

    selected, _shown, _unique = store.select_and_record(choose)
    results.put(selected)


class QuoteStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "ambient.sqlite3"
        self.legacy = self.root / "hook_state.json"
        self.quotes = [
            Quote("Debug calmly.", "Work A", "Author A", "", ["resilience"]),
            Quote("Build with care.", "Work B", "Author B", "", ["creativity"]),
        ]

    def test_legacy_positions_migrate_to_stable_ids_and_survive_reorder(self) -> None:
        self.legacy.write_text(
            json.dumps({"shown_counts": {"0": 3}, "recent_indices": [0]}),
            encoding="utf-8",
        )
        store = QuoteStateStore(self.db)
        ids = [quote_id(item) for item in self.quotes]
        store.migrate_legacy_indices(ids, self.legacy)
        counts, recent, _ = store.snapshot()
        self.assertEqual(counts[ids[0]], 3)
        self.assertEqual(recent, [ids[0]])

    def test_state_database_is_owner_read_write_only(self) -> None:
        QuoteStateStore(self.db).increment_counter("test")
        self.assertEqual(stat.S_IMODE(self.db.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.db.parent.stat().st_mode), 0o700)

    def test_concurrent_exposure_updates_are_not_lost(self) -> None:
        identifier = quote_id(self.quotes[0])

        def write_many(_: int) -> None:
            store = QuoteStateStore(self.db)
            for _ in range(20):
                store.record_selection(identifier)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(write_many, range(8)))

        counts, _recent, _feedback = QuoteStateStore(self.db).snapshot()
        self.assertEqual(counts[identifier], 160)

    def test_separate_processes_preserve_every_exposure(self) -> None:
        identifier = quote_id(self.quotes[0])
        context = multiprocessing.get_context("spawn")
        processes = [
            context.Process(target=_process_write, args=(str(self.db), identifier, 10))
            for _ in range(4)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=10)
            self.assertEqual(process.exitcode, 0)
        counts, _recent, _feedback = QuoteStateStore(self.db).snapshot()
        self.assertEqual(counts[identifier], 40)
        self.assertEqual(list(self.root.glob("ambient.sqlite3.corrupt-*")), [])

    def test_separate_processes_select_from_one_serialized_snapshot(self) -> None:
        identifiers = [f"quote-{index:02d}" for index in range(12)]
        context = multiprocessing.get_context("spawn")
        results = context.Queue()
        processes = [
            context.Process(
                target=_process_select_once,
                args=(str(self.db), identifiers, results),
            )
            for _ in identifiers
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=10)
            self.assertEqual(process.exitcode, 0)
        selected = [results.get(timeout=2) for _ in processes]
        self.assertEqual(len(set(selected)), len(identifiers))

    def test_compact_budget_excludes_oversized_quotes_instead_of_truncating(self) -> None:
        oversized = Quote("界" * (COMPACT_MAX_BYTES + 1), "Long", "Author", "", ["focus"])
        short = Quote("Focus.", "Short", "Author", "", ["focus"])
        self.assertEqual(select_quote_index([oversized, short], {}, [], ["focus"]), 1)

    def test_relevant_alternatives_do_not_repeat_inside_recent_window(self) -> None:
        quotes = [
            Quote(
                f"Keep a distinct focus {index}.",
                f"Work {index}",
                f"Author {index}",
                "",
                ["focus"],
            )
            for index in range(RECENT_WINDOW + 10)
        ]
        shown_counts: dict[str, int] = {}
        recent_ids: list[str] = []
        selected_ids: list[str] = []

        for _ in range(RECENT_WINDOW):
            index = select_quote_index(
                quotes,
                shown_counts,
                recent_ids,
                ["focus"],
                ambient_only=True,
            )
            identifier = quote_id(quotes[index])
            self.assertIn("focus", quotes[index].tags)
            selected_ids.append(identifier)
            shown_counts[identifier] = shown_counts.get(identifier, 0) + 1
            recent_ids = (recent_ids + [identifier])[-RECENT_WINDOW:]

        self.assertEqual(len(set(selected_ids)), RECENT_WINDOW)

    def test_ambient_budget_is_stricter_than_on_demand_delivery(self) -> None:
        ambient = Quote("Focus now.", "Short", "Author", "", ["focus"])
        byte_heavy = Quote("界" * 70, "Work", "Author", "", ["focus"])
        word_heavy = Quote(
            " ".join(["focus"] * (AMBIENT_MAX_WORDS + 1)),
            "Work",
            "Author",
            "",
            ["focus"],
        )

        byte_payload = {
            "text": byte_heavy.text,
            "author": byte_heavy.author,
            "book": byte_heavy.book_title,
        }
        self.assertLessEqual(
            len(format_quote_message(byte_payload).encode("utf-8")),
            COMPACT_MAX_BYTES,
        )
        self.assertGreater(
            len(format_quote_message(byte_payload).encode("utf-8")),
            AMBIENT_MAX_BYTES,
        )
        with self.assertRaises(ValueError):
            format_ambient_quote_message(byte_payload)
        with self.assertRaises(ValueError):
            format_ambient_quote_message(
                {
                    "text": word_heavy.text,
                    "author": word_heavy.author,
                    "book": word_heavy.book_title,
                }
            )
        self.assertEqual(
            select_quote_index(
                [byte_heavy, word_heavy, ambient],
                {},
                [],
                ["focus"],
                ambient_only=True,
            ),
            2,
        )

    def test_empty_catalog_has_the_public_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "no compact quotes"):
            select_quote_index([], {}, [])

    def test_negative_feedback_is_deterministic_tiebreaker(self) -> None:
        first = Quote("Hold steady.", "One", "Author A", "", ["focus"])
        second = Quote("Keep attention.", "Two", "Author B", "", ["focus"])
        self.assertEqual(
            select_quote_index(
                [first, second],
                {},
                [],
                ["focus"],
                feedback={quote_id(first): -1, quote_id(second): 1},
            ),
            1,
        )

    def test_corrupt_state_is_quarantined_and_requires_interactive_acknowledgement(self) -> None:
        self.db.write_bytes(b"not a sqlite database")
        store = QuoteStateStore(self.db)
        with self.assertRaises(StateRecoveryRequired):
            store.increment_counter("pi_turn_count")
        quarantined = list(self.root.glob("ambient.sqlite3.corrupt-*"))
        self.assertEqual(len(quarantined), 1)
        self.assertTrue(store.recovery_notice_pending())
        self.assertTrue(store.consume_recovery_notice())
        self.assertFalse(store.recovery_notice_pending())
        self.assertFalse(store.consume_recovery_notice())

    def test_corrupt_legacy_state_is_quarantined_before_migration(self) -> None:
        self.legacy.write_text("{not json", encoding="utf-8")
        store = QuoteStateStore(self.db)
        with self.assertRaises(StateRecoveryRequired):
            store.migrate_legacy_indices([quote_id(item) for item in self.quotes], self.legacy)
        self.assertEqual(len(list(self.root.glob("hook_state.json.corrupt-*"))), 1)
        self.assertTrue(store.recovery_notice_pending())


if __name__ == "__main__":
    unittest.main()
