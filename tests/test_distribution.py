"""Keep standalone package and agent manifests internally consistent."""

from __future__ import annotations

import json
import os
import shutil
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
        self.assertIn('version = "1.2.0"', pyproject)
        self.assertIn("dependencies = []", pyproject)

        for path in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            "package.json",
        ):
            self.assertEqual(self._json(path)["version"], "1.2.0", path)

        marketplace = self._json(".claude-plugin/marketplace.json")
        self.assertEqual(marketplace["plugins"][0]["version"], "1.2.0")
        self.assertIn("version: 1.2.0", (ROOT / "plugin.yaml").read_text(encoding="utf-8"))
        self.assertIn('__version__ = "1.2.0"', (ROOT / "bookshelf" / "__init__.py").read_text(encoding="utf-8"))

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

    def test_host_manifests_declare_their_own_portable_hook_roots(self) -> None:
        claude_hook = self._json("hooks/hooks.json")
        codex_hook = self._json("hooks/codex-hooks.json")
        claude_command = claude_hook["hooks"]["Stop"][0]["hooks"][0]["command"]
        codex_command = codex_hook["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("CLAUDE_PLUGIN_ROOT", claude_command)
        self.assertIn("PLUGIN_ROOT", codex_command)
        for command, host in ((claude_command, "claude"), (codex_command, "codex")):
            self.assertIn("env -i", command)
            self.assertIn(f"--host {host}", command)
            self.assertIn("BOOKSHELF_DATA_HOME", command)
            self.assertNotIn("env |", command)
        self.assertEqual(self._json(".claude-plugin/plugin.json")["hooks"], "./hooks/hooks.json")
        self.assertEqual(self._json(".codex-plugin/plugin.json")["hooks"], "./hooks/codex-hooks.json")
        self.assertEqual(self._json(".codex-plugin/plugin.json")["skills"], "./skills/")
        script = ROOT / "hooks" / "ambient.py"
        self.assertTrue(script.is_file())
        self.assertIn("except Exception", script.read_text(encoding="utf-8"))

    def test_protocol_contract_is_shipped_as_inert_data(self) -> None:
        schema = self._json("protocol/ambient-companion-v1.schema.json")
        example = self._json("protocol/ambient-companion-v1.example.json")
        self.assertEqual(example["protocol_version"], schema["properties"]["protocol_version"]["const"])
        self.assertIn(example["host"], schema["properties"]["host"]["enum"])
        self.assertEqual(example["event"], schema["properties"]["event"]["const"])
        self.assertIn(example["mode"], schema["properties"]["mode"]["enum"])
        self.assertLessEqual(len(example["intent_tags"]), schema["properties"]["intent_tags"]["maxItems"])
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("ambient-companion-v1.schema.json", pyproject)
        self.assertIn("ambient-companion-v1.example.json", pyproject)

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
            isolated_plugin = temp_root / "isolated-plugin"
            shutil.copytree(ROOT / "bookshelf", isolated_plugin / "bookshelf")
            shutil.copytree(ROOT / "skills", isolated_plugin / "skills")
            home = temp_root / "home"
            working_directory = temp_root / "unrelated-project"
            home.mkdir()
            working_directory.mkdir()
            env = {"HOME": str(home), "PATH": "", "XDG_DATA_HOME": str(home / "data")}
            completed = subprocess.run(
                [sys.executable, str(isolated_plugin / "skills" / "bookshelf" / "scripts" / "quote.py"), "--json"],
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
