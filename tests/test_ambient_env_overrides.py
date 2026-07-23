"""The sandboxed hook env vars must actually steer ambient behavior.

hooks/hooks.json, hooks/codex-hooks.json, and extensions/bookshelf.ts
allow-list BOOKSHELF_AMBIENT_ENABLED, BOOKSHELF_AMBIENT_CADENCE, and
BOOKSHELF_DATA_HOME into the scrubbed hook environment; these tests pin the
contract: env override → config file → default, blank or invalid values fall
through, and the data-home override redirects the whole state surface.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bookshelf import storage
from bookshelf.platform import app_data_dir
from bookshelf.skill import quote_state
from bookshelf.skill.config import get_ambient_cadence, is_ambient_enabled

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env(**overrides: str) -> mock._patch_dict:
    return mock.patch.dict("os.environ", overrides, clear=False)


class AmbientEnabledOverrideTests(unittest.TestCase):
    def test_env_false_beats_config_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _env(BOOKSHELF_DATA_HOME=tmp, BOOKSHELF_AMBIENT_ENABLED="0"):
                storage.save_config({"ambient_enabled": True})
                self.assertFalse(is_ambient_enabled())

    def test_env_true_beats_config_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _env(BOOKSHELF_DATA_HOME=tmp, BOOKSHELF_AMBIENT_ENABLED="true"):
                storage.save_config({"ambient_enabled": False})
                self.assertTrue(is_ambient_enabled())

    def test_blank_and_invalid_fall_through_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for raw in ("", "banana"):
                with self.subTest(raw=raw):
                    with _env(BOOKSHELF_DATA_HOME=tmp, BOOKSHELF_AMBIENT_ENABLED=raw):
                        storage.save_config({"ambient_enabled": True})
                        self.assertTrue(is_ambient_enabled())


class AmbientCadenceOverrideTests(unittest.TestCase):
    def test_env_cadence_beats_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _env(BOOKSHELF_DATA_HOME=tmp, BOOKSHELF_AMBIENT_CADENCE="2"):
                storage.save_config({"ambient_cadence": 7})
                self.assertEqual(get_ambient_cadence("codex"), 2)

    def test_blank_and_invalid_fall_through_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for raw in ("", "0", "-3", "x"):
                with self.subTest(raw=raw):
                    with _env(BOOKSHELF_DATA_HOME=tmp, BOOKSHELF_AMBIENT_CADENCE=raw):
                        storage.save_config({"ambient_cadence": 7})
                        self.assertEqual(get_ambient_cadence("codex"), 7)


class DataHomeOverrideTests(unittest.TestCase):
    def test_data_home_redirects_the_whole_state_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _env(BOOKSHELF_DATA_HOME=tmp):
                target = Path(tmp)
                self.assertEqual(app_data_dir("bookshelf"), target)
                self.assertEqual(storage.data_dir(), target)
                self.assertEqual(quote_state.state_db_path().parent, target)

    def test_explicit_base_dir_still_beats_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _env(BOOKSHELF_DATA_HOME=tmp):
                explicit = Path(tmp) / "explicit"
                self.assertEqual(app_data_dir("bookshelf", explicit), explicit)

    def test_blank_value_means_unset(self) -> None:
        with _env(BOOKSHELF_DATA_HOME=""):
            self.assertNotEqual(app_data_dir("bookshelf"), Path("."))


class HookEndToEndOverrideTests(unittest.TestCase):
    def test_hook_process_honors_all_three_overrides(self) -> None:
        """Enabled + cadence 1 via env, state confined to the env data home."""
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "hooks" / "ambient.py"), "--host", "codex"],
                input='{"hook_event_name": "Stop"}',
                capture_output=True,
                text=True,
                timeout=30,
                cwd=PROJECT_ROOT,
                env={
                    "PATH": "/usr/bin:/bin",
                    "BOOKSHELF_DATA_HOME": tmp,
                    "BOOKSHELF_AMBIENT_ENABLED": "1",
                    "BOOKSHELF_AMBIENT_CADENCE": "1",
                    "PYTHONUTF8": "1",
                },
            )
            payload = json.loads(proc.stdout)
            self.assertIn("systemMessage", payload)
            self.assertTrue(
                (Path(tmp) / quote_state.DB_FILENAME).exists(),
                "state DB must be created inside BOOKSHELF_DATA_HOME",
            )


if __name__ == "__main__":
    unittest.main()
