"""Static safety and content checks for the Pagecast handoff bundle."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "site" / "pagecast"
HTML = (BUNDLE / "index.html").read_text(encoding="utf-8")
MANIFEST = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))


class PagecastBundleTests(unittest.TestCase):
    def test_bundle_has_the_expected_static_assets_and_media_contract(self) -> None:
        for relative_path in MANIFEST["expected_assets"]:
            self.assertTrue((BUNDLE / relative_path.removeprefix("./")).is_file(), relative_path)
        self.assertEqual(
            MANIFEST["final_media_expected"],
            ["./assets/bookshelf-demo.mp4", "./assets/bookshelf-poster.png"],
        )
        for relative_path, expected in MANIFEST["assets"].items():
            asset = BUNDLE / relative_path.removeprefix("./")
            self.assertTrue(asset.is_file(), relative_path)
            payload = asset.read_bytes()
            self.assertEqual(len(payload), expected["bytes"], relative_path)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), expected["sha256"], relative_path)

    def test_pagecast_story_and_accessibility_markers(self) -> None:
        self.assertIn("<title>Bookshelf — Book quotes inside Codex and Claude Code</title>", HTML)
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", HTML)), 1)
        for marker in (
            'href="#main"',
            "Accessible transcript",
            "bookshelf quote --intent refactor",
            "bookshelf feedback up|down",
            'tabindex="-1"',
            "./assets/bookshelf-demo.mp4",
            "./assets/bookshelf-poster.png",
            "3,124",
            "3,111",
            "1,117",
            "949",
            "585",
            "2,539",
            "Instead of staring at another tool call",
            "Codex Desktop + CLI",
            "Claude Code",
            "Pi + Hermes",
            "@media (max-width: 390px)",
            "prefers-reduced-motion: reduce",
            "focus-visible",
        ):
            self.assertIn(marker, HTML)

    def test_pagecast_has_final_canonical_and_social_metadata(self) -> None:
        page_url = "https://bookshelf-8dz.pages.dev/"
        self.assertIn(f'<link rel="canonical" href="{page_url}">', HTML)
        self.assertIn(f'<meta property="og:url" content="{page_url}">', HTML)
        self.assertIn('<meta property="og:type" content="website">', HTML)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', HTML)
        self.assertIn(
            f'<meta property="og:image" content="{page_url}assets/bookshelf-poster.png">',
            HTML,
        )

    def test_assets_are_local_and_pagecast_has_no_hosting_or_auth_markers(self) -> None:
        for value in re.findall(r'(?:src|poster)="([^"]+)"', HTML):
            self.assertTrue(value.startswith("./assets/"), value)
        self.assertNotRegex(HTML, r"url\(\s*['\"]?/")
        self.assertNotRegex(HTML, r"(?:src|poster)=['\"]https?://")
        lowered = HTML.casefold()
        for forbidden in ("chatgpt", "openai", "chatgpt.site", ".openai", "worker", "drizzle", "fetch("):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
