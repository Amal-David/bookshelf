"""Release gates for the deterministic Bookshelf ranker."""

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from bookshelf.skill.evaluation import SELECTION_P95_RELEASE_MAX_MS, run_evaluation


class RelevanceEvaluationTests(unittest.TestCase):
    def test_versioned_fixture_meets_quality_and_latency_gates(self) -> None:
        metrics = run_evaluation()
        self.assertGreaterEqual(metrics["events"], 160)
        self.assertGreaterEqual(metrics["relevance_gain_points"], 10.0)
        self.assertLess(metrics["wrong_context_p_at_1"], 5.0)
        self.assertGreaterEqual(metrics["neutral_correctness"], 90.0)
        self.assertLess(
            metrics["selection_p95_ms_10000"],
            SELECTION_P95_RELEASE_MAX_MS,
        )
        for result in metrics["per_intent"].values():
            self.assertGreaterEqual(result["p_at_1"] - result["legacy_p_at_1"], -3.0)

    def test_novelty_first_and_random_selection_cannot_clear_the_gate(self) -> None:
        def novelty_first(quotes, shown_counts, recent_indices, context_tags):
            del shown_counts, recent_indices, context_tags
            return 0

        def deterministic_random(quotes, shown_counts, recent_indices, context_tags):
            del shown_counts, recent_indices
            digest = hashlib.sha256("|".join(context_tags or ()).encode("utf-8")).digest()
            return int.from_bytes(digest[:4], "big") % len(quotes)

        for selector in (novelty_first, deterministic_random):
            metrics = run_evaluation(selector=selector)
            self.assertTrue(
                metrics["relevance_p_at_1"] < 90.0
                or metrics["wrong_context_p_at_1"] >= 5.0
                or metrics["relevance_gain_points"] < 10.0,
                metrics,
            )

    def test_adversarial_labels_reject_substring_intent_matching(self) -> None:
        def substring_normalizer(metadata):
            text = " ".join(metadata.values()).casefold()
            if "debug" in text:
                return ["debug"]
            return ["neutral"]

        with patch("bookshelf.skill.evaluation.normalize_event", substring_normalizer):
            with self.assertRaisesRegex(ValueError, "normalization drift"):
                run_evaluation()


if __name__ == "__main__":
    unittest.main()
