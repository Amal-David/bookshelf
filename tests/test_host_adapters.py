"""Focused contract tests for the Python host adapters."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HostAdapterTests(unittest.TestCase):
    def test_shared_hook_surfaces_an_event_banner(self) -> None:
        hook = _load_module("bookshelf_shared_hook", ROOT / "hooks" / "ambient.py")
        output = io.StringIO()
        with mock.patch(
            "bookshelf.ambient.ambient_message",
            return_value="A due quote",
        ), mock.patch("sys.stdin", io.StringIO("{}")), mock.patch(
            "sys.stdout",
            output,
        ), mock.patch.dict(
            os.environ,
            {"PLUGIN_ROOT": str(ROOT)},
            clear=False,
        ):
            self.assertEqual(hook.main([]), 0)

        self.assertEqual(
            json.loads(output.getvalue()),
            {"systemMessage": "A due quote"},
        )

    def test_hermes_registers_hook_and_canonical_skill(self) -> None:
        plugin = _load_module("bookshelf_hermes_plugin", ROOT / "__init__.py")

        class Context:
            hooks: list[tuple] = []
            skills: list[tuple] = []

            def register_hook(self, *args) -> None:
                self.hooks.append(args)

            def register_skill(self, *args) -> None:
                self.skills.append(args)

        context = Context()
        plugin.register(context)
        self.assertEqual(context.hooks[0][0], "transform_llm_output")
        self.assertEqual(context.skills[0][0], "bookshelf")
        self.assertEqual(
            context.skills[0][1],
            ROOT / "skills" / "bookshelf" / "SKILL.md",
        )

    def test_hermes_transform_is_opt_in_and_non_destructive(self) -> None:
        plugin = _load_module("bookshelf_hermes_transform", ROOT / "__init__.py")
        with mock.patch(
            "bookshelf.ambient.ambient_message",
            return_value=None,
        ):
            self.assertIsNone(plugin._transform_llm_output("Original"))
        with mock.patch(
            "bookshelf.ambient.ambient_message",
            return_value="A due quote",
        ):
            self.assertEqual(
                plugin._transform_llm_output("Original"),
                "Original\n\nA due quote",
            )


if __name__ == "__main__":
    unittest.main()
