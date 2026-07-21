"""Ambient delivery must be opt-in, paced, and fail-safe."""

from __future__ import annotations

import socket
import unittest
from unittest import mock

from bookshelf import ambient


class AmbientDeliveryTests(unittest.TestCase):
    def test_disabled_mode_does_not_touch_state(self) -> None:
        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            return_value=False,
        ), mock.patch("bookshelf.skill.quote_state.QuoteStateStore.increment_counter") as increment:
            self.assertIsNone(ambient.ambient_quote("pi"))
        increment.assert_not_called()

    def test_each_host_uses_a_persistent_cadence_counter(self) -> None:
        quote = {"text": "Keep going."}

        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            return_value=True,
        ), mock.patch(
            "bookshelf.skill.quote_state.QuoteStateStore.increment_counter",
            side_effect=[1, 2],
        ), mock.patch.object(
            ambient,
            "get_ambient_cadence",
            return_value=2,
        ), mock.patch.object(
            ambient,
            "pick_quote",
            return_value=quote,
        ) as pick:
            self.assertIsNone(ambient.ambient_quote("pi"))
            self.assertEqual(ambient.ambient_quote("pi"), quote)

        pick.assert_called_once_with([], ambient_only=True)

    def test_configured_intent_guides_ambient_selection_without_terminal_content(self) -> None:
        quote = {"text": "Make it simpler."}

        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            return_value=True,
        ), mock.patch(
            "bookshelf.skill.quote_state.QuoteStateStore.increment_counter",
            return_value=5,
        ), mock.patch.object(
            ambient,
            "get_ambient_cadence",
            return_value=5,
        ), mock.patch.object(
            ambient,
            "get_ambient_intent",
            return_value="refactor",
        ), mock.patch.object(
            ambient,
            "pick_quote",
            return_value=quote,
        ) as pick:
            self.assertEqual(ambient.ambient_quote("claude"), quote)

        pick.assert_called_once_with(
            ["simplicity", "discipline", "focus"],
            ambient_only=True,
        )

    def test_adapter_error_never_escapes(self) -> None:
        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            side_effect=OSError("unavailable"),
        ):
            self.assertIsNone(ambient.ambient_message("hermes"))

    def test_ambient_selection_never_attempts_network_access(self) -> None:
        quote = {"text": "Stay local."}
        with mock.patch.object(ambient, "is_ambient_enabled", return_value=True), mock.patch(
            "bookshelf.skill.quote_state.QuoteStateStore.increment_counter", return_value=1
        ), mock.patch.object(ambient, "get_ambient_cadence", return_value=1), mock.patch.object(
            ambient, "pick_quote", return_value=quote
        ), mock.patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
            self.assertEqual(ambient.ambient_quote("pi"), quote)


if __name__ == "__main__":
    unittest.main()
