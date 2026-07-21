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
        config = {"ambient_enabled": False, "ambient_cadence": 5}

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
            result = cli.main(["ambient", "enable", "--cadence", "9"])

        self.assertEqual(result, 0)
        self.assertTrue(config["ambient_enabled"])
        self.assertEqual(config["ambient_cadence"], 9)
        self.assertIn("enabled", output.getvalue())

    def test_no_arguments_preserves_the_terminal_browser(self) -> None:
        with mock.patch("bookshelf.app.run") as run:
            self.assertEqual(cli.main([]), 0)
        run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
