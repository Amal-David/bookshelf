"""Keep standalone package and agent manifests internally consistent."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DistributionMetadataTests(unittest.TestCase):
    def _json(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_release_identity_matches_every_manifest(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "ambient-bookshelf"', pyproject)
        self.assertIn('version = "1.0.0"', pyproject)
        self.assertIn("dependencies = []", pyproject)

        for path in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            "package.json",
        ):
            self.assertEqual(self._json(path)["version"], "1.0.0", path)

    def test_codex_marketplace_points_to_root_plugin(self) -> None:
        marketplace = self._json(".agents/plugins/marketplace.json")
        plugin = marketplace["plugins"][0]
        self.assertEqual(plugin["name"], "bookshelf")
        self.assertEqual(plugin["source"]["path"], "./")
        self.assertTrue((ROOT / ".codex-plugin" / "plugin.json").is_file())

    def test_pi_package_has_no_runtime_dependencies(self) -> None:
        package = self._json("package.json")
        self.assertNotIn("dependencies", package)
        self.assertIn("pi-package", package["keywords"])
        extension = (ROOT / package["pi"]["extensions"][0]).read_text(encoding="utf-8")
        self.assertIn('pi.on("agent_end"', extension)
        self.assertIn("ctx.ui.notify", extension)

    def test_plugin_hook_is_shared_and_fail_safe(self) -> None:
        hook = self._json("hooks/hooks.json")
        command = hook["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("CLAUDE_PLUGIN_ROOT", command)
        script = ROOT / "hooks" / "ambient.py"
        self.assertTrue(script.is_file())
        self.assertIn("except Exception", script.read_text(encoding="utf-8"))

    def test_standalone_python_has_no_umbrella_imports(self) -> None:
        offenders = []
        umbrella_name = "terminal" + "_arcade"
        for path in (ROOT / "bookshelf").rglob("*.py"):
            if umbrella_name in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(ROOT))
        self.assertEqual(offenders, [])

    def test_canonical_skill_quote_command_uses_shipped_wrapper(self) -> None:
        skill = (ROOT / "skills" / "bookshelf" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'python3 "<skill-dir>/scripts/quote.py" --json',
            skill,
        )
        script = ROOT / "skills" / "bookshelf" / "scripts" / "quote.py"
        self.assertTrue(script.is_file(), f"skill wrapper is not shipped: {script}")

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            home = temp_root / "home"
            working_directory = temp_root / "unrelated-project"
            home.mkdir()
            working_directory.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            completed = subprocess.run(
                [sys.executable, str(script), "--json"],
                cwd=working_directory,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

        quote = json.loads(completed.stdout)
        self.assertTrue(quote["text"])
        self.assertTrue(quote["author"])
        self.assertTrue(quote["book"])


if __name__ == "__main__":
    unittest.main()
