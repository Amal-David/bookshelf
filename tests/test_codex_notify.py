import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bookshelf.skill.codex_notify as codex_notify


class CodexNotifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
    def test_turn_ended_surfaces_a_due_opt_in_quote_on_macos(self) -> None:
        with patch.object(codex_notify.sys, "platform", "darwin"), patch.object(
            codex_notify.subprocess, "run"
        ) as run_mock, patch("bookshelf.ambient.ambient_message", return_value="A due quote"):
            codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        self.assertEqual(run_mock.call_count, 1)
        for call in run_mock.call_args_list:
            cmd = call.args[0]
            self.assertEqual(cmd[0], "osascript")
            self.assertIn("display notification", cmd[2])

    def test_non_turn_ended_events_are_noops(self) -> None:
        with patch.object(codex_notify.subprocess, "run") as run_mock:
            for event in ("turn-started", "session-started", "tool-called", ""):
                codex_notify.main(["codex_notify.py", event, "{}"])

        run_mock.assert_not_called()
    def test_disabled_legacy_adapter_is_a_silent_noop(self) -> None:
        with patch.object(codex_notify.subprocess, "run") as run_mock, patch(
            "bookshelf.ambient.ambient_message", return_value=None
        ):
            self.assertEqual(codex_notify.main(["codex_notify.py", "turn-ended", "{}"]), 0)
        run_mock.assert_not_called()

    def test_non_macos_falls_back_to_stderr(self) -> None:
        captured = []

        def fake_write(text: str) -> int:
            captured.append(text)
            return len(text)

        with patch.object(codex_notify.sys, "platform", "linux"), patch.object(
            codex_notify.sys.stderr, "write", side_effect=fake_write
        ), patch.object(codex_notify.subprocess, "run") as run_mock, patch(
            "bookshelf.ambient.ambient_message", return_value="A due quote"
        ):
            codex_notify.main(["codex_notify.py", "turn-ended", "{}"])

        run_mock.assert_not_called()
        self.assertEqual(captured, ["A due quote\n"])


if __name__ == "__main__":
    unittest.main()
