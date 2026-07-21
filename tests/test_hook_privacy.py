"""Privacy boundary tests for the ambient hook protocol."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bookshelf.skill import hook, quote_picker
from bookshelf.skill.quote_state import QuoteStateStore


class _BinaryStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


class HookPrivacyTests(unittest.TestCase):
    def test_oversized_and_malformed_payloads_do_not_update_state(self) -> None:
        for payload in (b"{" * 20, b"x" * (hook.HOOK_INPUT_MAX_BYTES + 1), b"\xff"):
            output = io.StringIO()
            with mock.patch.object(hook.sys, "stdin", _BinaryStdin(payload)), mock.patch.object(
                hook.sys, "stdout", output
            ), mock.patch(
                "bookshelf.skill.quote_state.QuoteStateStore.increment_counter"
            ) as increment:
                hook.main()
            self.assertEqual(json.loads(output.getvalue()), {})
            increment.assert_not_called()

    def test_secret_bearing_raw_fields_never_reach_sqlite_or_delivery(self) -> None:
        sentinel = "SECRET_SENTINEL_DO_NOT_STORE"
        with tempfile.TemporaryDirectory() as temporary:
            store = QuoteStateStore(Path(temporary) / "state.sqlite3")
            with mock.patch.object(quote_picker, "_state_store", return_value=store):
                tags = quote_picker.get_context_tags(
                    {"tool_name": "Bash", "command": f"debug {sentinel}", "file_path": sentinel}
                )
                quote = quote_picker.pick_quote(tags)
            self.assertIsNotNone(quote)
            self.assertNotIn(sentinel, (Path(temporary) / "state.sqlite3").read_bytes().decode("latin1"))
            self.assertNotIn(sentinel, quote_picker.format_quote_message(quote))

    def test_adversarial_substrings_fall_back_to_neutral(self) -> None:
        for label in ("relationship", "debugger", "passive", "rebuilding"):
            self.assertEqual(quote_picker.normalize_event({"tool_name": label}), ["neutral"])


if __name__ == "__main__":
    unittest.main()
