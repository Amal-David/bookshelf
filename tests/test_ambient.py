"""Ambient delivery must be opt-in, paced, and fail-safe."""

from __future__ import annotations

import unittest
from unittest import mock

from bookshelf import ambient


class AmbientDeliveryTests(unittest.TestCase):
    def test_disabled_mode_does_not_touch_state(self) -> None:
        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            return_value=False,
        ), mock.patch.object(ambient, "load_hook_state") as load:
            self.assertIsNone(ambient.ambient_quote("pi"))
        load.assert_not_called()

    def test_each_host_uses_a_persistent_cadence_counter(self) -> None:
        state: dict = {}
        quote = {"text": "Keep going."}

        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            return_value=True,
        ), mock.patch.object(
            ambient,
            "load_hook_state",
            side_effect=lambda: dict(state),
        ), mock.patch.object(
            ambient,
            "save_hook_state",
            side_effect=lambda updated: state.update(updated),
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

        self.assertEqual(state["pi_turn_count"], 2)
        pick.assert_called_once_with(None)

    def test_adapter_error_never_escapes(self) -> None:
        with mock.patch.object(
            ambient,
            "is_ambient_enabled",
            side_effect=OSError("unavailable"),
        ):
            self.assertIsNone(ambient.ambient_message("hermes"))


if __name__ == "__main__":
    unittest.main()
