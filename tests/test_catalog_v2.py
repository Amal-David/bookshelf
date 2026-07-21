"""Integrity gates for the generated, provenance-aware v2 catalog."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from bookshelf.data.catalog import counts, provenance_for
from bookshelf.data.catalog_v2 import load_catalog_v2
from bookshelf.data.quotes import LEGACY_QUOTES, QUOTES
from bookshelf.skill.quote_picker import quote_id, work_id
from scripts.compile_catalog import validate_new_records


ROOT = Path(__file__).resolve().parents[1]


class CatalogV2Tests(unittest.TestCase):
    def test_generated_counts_clear_release_floor_and_distinguish_works(self) -> None:
        catalog_counts = counts()
        self.assertGreaterEqual(catalog_counts["unique_normalized_quotes"], 3_100)
        self.assertGreaterEqual(catalog_counts["catalogued_books"], 1_100)
        self.assertNotEqual(catalog_counts["catalogued_books"], catalog_counts["quoted_works"])
        self.assertEqual(catalog_counts["quotes"], len(QUOTES))

    def test_every_v2_quote_has_primary_source_metadata_and_review_boundary(self) -> None:
        catalog = load_catalog_v2()
        self.assertEqual(len(catalog["quotes"]), 585)
        self.assertEqual(len(catalog["books"]), 117)
        work_ids = {book["work_id"] for book in catalog["books"]}
        for record in catalog["quotes"]:
            self.assertIn(record["work_id"], work_ids)
            self.assertTrue(record["quote_id"].startswith("quote_se_"))
            self.assertTrue(record["source_identifier"].startswith("standardebooks/"))
            self.assertEqual(record["rights_class"], "public-domain-us")
            self.assertEqual(record["verification_state"], "source-linked-review-pending")
            self.assertEqual(record["admission_state"], "review-pending-human-review")
            self.assertEqual(len(record["digest_sha256"]), 64)
            self.assertEqual(len(record["extraction_snapshot_sha256"]), 64)
            self.assertEqual(record["source_url"], record["source_repository_url"])

    def test_primary_source_ids_survive_runtime_ranking(self) -> None:
        primary = next(quote for quote in QUOTES if quote.quote_id.startswith("quote_se_"))
        self.assertEqual(quote_id(primary), primary.quote_id)
        self.assertEqual(work_id(primary), primary.work_id)

    def test_legacy_records_stay_explicitly_unverified(self) -> None:
        legacy = provenance_for(LEGACY_QUOTES[0])
        self.assertEqual(legacy["verification_state"], "legacy-unverified")
        self.assertEqual(legacy["admission_state"], "legacy")
        self.assertEqual(legacy["rights_class"], "legacy-unknown")
        self.assertFalse(
            any("parsing be broken" in quote.text for quote in LEGACY_QUOTES),
            "legacy catalog must not ship the known malformed quote text",
        )

    def test_generated_count_document_matches_manifest(self) -> None:
        manifest = json.loads((ROOT / "bookshelf/data/catalog_manifest.json").read_text())
        documentation = (ROOT / "docs/catalog-counts.md").read_text()
        self.assertIn(f"**{manifest['counts']['quotes']:,} shipped quote records**", documentation)
        self.assertIn(f"**{manifest['counts']['quoted_works']:,} works referenced by quotes**", documentation)

    def test_compiler_rejects_bidirectional_override_controls(self) -> None:
        catalog = load_catalog_v2()
        for control in ("\u202e", "\t"):
            with self.subTest(control=repr(control)):
                unsafe = deepcopy(catalog["quotes"][0])
                unsafe["text"] = f"{unsafe['text']}{control}"
                with self.assertRaisesRegex(ValueError, "unsafe control character"):
                    validate_new_records([unsafe], catalog["books"])

    def test_compiler_requires_exact_source_linkage_and_snapshot_metadata(self) -> None:
        catalog = load_catalog_v2()
        for field in (
            "source_repository_url",
            "extraction_snapshot_sha256",
            "verification_method",
        ):
            with self.subTest(missing=field):
                incomplete = deepcopy(catalog["quotes"][0])
                incomplete.pop(field)
                with self.assertRaisesRegex(ValueError, "missing required quote metadata"):
                    validate_new_records([incomplete], catalog["books"])

        mismatched = deepcopy(catalog["quotes"][0])
        mismatched["source_url"] = "https://github.com/standardebooks/not-the-record-source"
        with self.assertRaisesRegex(ValueError, "mismatched source repository"):
            validate_new_records([mismatched], catalog["books"])

        bad_snapshot = deepcopy(catalog["quotes"][0])
        bad_snapshot["extraction_snapshot_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "invalid extraction snapshot digest"):
            validate_new_records([bad_snapshot], catalog["books"])


if __name__ == "__main__":
    unittest.main()
