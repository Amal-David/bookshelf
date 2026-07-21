"""Focused tests for Bookshelf's public CLI."""

from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from bookshelf import cli


class BookshelfCliTests(unittest.TestCase):
    def test_quote_json_has_stable_public_fields(self) -> None:
        quote = {
            "text": "A useful line.",
            "author": "An Author",
            "book": "A Book",
            "tags": ["focus"],
        }
        output = io.StringIO()
        with mock.patch(
            "bookshelf.skill.quote_picker.pick_quote",
            return_value=quote,
        ), mock.patch("sys.stdout", output):
            result = cli.main(["quote", "--json", "--tag", "focus"])

        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue()), quote)

    def test_ambient_enable_is_explicit_and_configurable(self) -> None:
        config = {
            "ambient_enabled": False,
            "ambient_cadence": 5,
            "ambient_intent": "neutral",
        }

        def save(updated: dict) -> None:
            config.update(updated)

        output = io.StringIO()
        with mock.patch(
            "bookshelf.storage.load_config",
            return_value=dict(config),
        ), mock.patch(
            "bookshelf.storage.save_config",
            side_effect=save,
        ), mock.patch("sys.stdout", output):
            result = cli.main(
                [
                    "ambient",
                    "enable",
                    "--cadence",
                    "9",
                    "--intent",
                    "refactor",
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue(config["ambient_enabled"])
        self.assertEqual(config["ambient_cadence"], 9)
        self.assertEqual(config["ambient_intent"], "refactor")
        self.assertIn("enabled", output.getvalue())
        self.assertIn("Theme: refactor", output.getvalue())

    def test_no_arguments_preserves_the_terminal_browser(self) -> None:
        with mock.patch("bookshelf.app.run") as run:
            self.assertEqual(cli.main([]), 0)
        run.assert_called_once_with()

    def test_corrupt_companion_state_reports_one_interactive_notice(self) -> None:
        store = mock.Mock()
        store.consume_recovery_notice.side_effect = [False, True]
        output = io.StringIO()
        with mock.patch("bookshelf.skill.quote_state.QuoteStateStore", return_value=store), mock.patch(
            "bookshelf.skill.quote_picker.pick_quote", return_value=None
        ), mock.patch("sys.stderr", output):
            self.assertEqual(cli.main(["quote"]), 1)
        self.assertEqual(store.consume_recovery_notice.call_count, 2)
        self.assertEqual(output.getvalue().count("recovered local companion state"), 1)


if __name__ == "__main__":
    unittest.main()
