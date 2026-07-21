"""Real host discovery is isolated; model-backed turns require explicit opt-in."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HOSTS = {
    "codex": "/opt/homebrew/bin/codex",
    "claude": "/Users/amal/.local/bin/claude",
    "pi": "/opt/homebrew/bin/pi",
    "hermes": "/Users/amal/.local/bin/hermes",
}
ROOT = Path(__file__).resolve().parents[1]


class RealHostDiscoveryTests(unittest.TestCase):
    def _discover(self, host: str) -> None:
        executable = os.environ.get(
            f"BOOKSHELF_{host.upper()}_BIN",
            HOSTS[host],
        )
        if not os.path.isfile(executable) and shutil.which(host) is None:
            self.skipTest(f"{host} CLI unavailable; no genuine host discovery possible")
        with tempfile.TemporaryDirectory() as temporary:
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": temporary,
                "XDG_DATA_HOME": os.path.join(temporary, "data"),
                "TMPDIR": temporary,
                "LANG": "C",
                "PI_CODING_AGENT_DIR": os.path.join(temporary, "pi"),
                "PI_OFFLINE": "1",
            }
            result = subprocess.run(
                [executable if os.path.isfile(executable) else host, "--version"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((result.stdout + result.stderr).strip())

    def test_codex_discovery(self) -> None:
        self._discover("codex")

    def test_claude_discovery(self) -> None:
        self._discover("claude")

    def test_pi_discovery(self) -> None:
        self._discover("pi")

    def test_hermes_discovery(self) -> None:
        self._discover("hermes")

    def test_real_hermes_loader_registers_namespaced_plugin_from_clean_cwd(self) -> None:
        python = os.environ.get("BOOKSHELF_HERMES_PYTHON")
        if not python or not os.path.isfile(python):
            self.skipTest("set BOOKSHELF_HERMES_PYTHON to the Hermes 0.16 Python")
        program = """
import os
import sys
from hermes_cli.plugins import PluginManager, PluginManifest

root = os.environ["PLUGIN_UNDER_TEST"]
manager = PluginManager()
manifest = PluginManifest(
    name="bookshelf",
    source="user",
    path=root,
    key="bookshelf",
)
manager._load_plugin(manifest)
loaded = manager._plugins["bookshelf"]
assert loaded.enabled, loaded.error
assert "transform_llm_output" in manager._hooks
assert "bookshelf:bookshelf" in manager._plugin_skills
manager.invoke_hook("transform_llm_output", response_text="Done.")
assert "bookshelf.ambient" in sys.modules
"""
        with tempfile.TemporaryDirectory() as temporary:
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": temporary,
                "XDG_DATA_HOME": os.path.join(temporary, "data"),
                "PLUGIN_UNDER_TEST": str(ROOT),
            }
            result = subprocess.run(
                [python, "-c", program],
                cwd=temporary,
                env=environment,
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(
    os.environ.get("BOOKSHELF_REAL_HOST_SMOKE") == "1",
    "real one-turn smoke skipped: it needs an isolated authenticated model host",
)
class RealHostOneTurnTests(unittest.TestCase):
    def test_opted_in_harness_required(self) -> None:
        self.skipTest(
            "set BOOKSHELF_REAL_HOST_SMOKE=1 only with a dedicated one-turn host harness"
        )
