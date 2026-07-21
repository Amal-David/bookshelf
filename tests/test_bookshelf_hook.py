import unittest

from bookshelf.data.quotes import QUOTES, Quote
from bookshelf.skill.hook import format_quote_message, get_context_tags, select_quote_index


class BookshelfHookTests(unittest.TestCase):
    def test_select_quote_index_prefers_relevance_before_unseen_novelty(self) -> None:
        quotes = [
            Quote("Seen quote", "Book A", "Author A", "", ["focus"]),
            Quote("Unseen quote 1", "Book B", "Author B", "", []),
            Quote("Unseen quote 2", "Book C", "Author C", "", []),
        ]

        idx = select_quote_index(
            quotes,
            shown_counts={"0": 4},
            recent_indices=[],
            context_tags=["focus"],
        )

        self.assertEqual(idx, 0)

    def test_format_quote_message_is_compact_by_default(self) -> None:
        message = format_quote_message(
            {
                "text": "Stay hungry, stay foolish.",
                "author": "Steve Jobs",
                "book": "Collected Talks",
                "tags": ["ambition", "creativity"],
                "unique_shown": 12,
            },
            len(QUOTES),
        )

        self.assertEqual(message, "“Stay hungry, stay foolish.” — Steve Jobs, Collected Talks")
        self.assertLessEqual(len(message.encode("utf-8")), 360)

    def test_event_normalization_uses_word_boundaries_not_raw_command_data(self) -> None:
        self.assertEqual(get_context_tags({"tool_name": "relationship"}), [])
        self.assertIn("resilience", get_context_tags({"tool_name": "debug tool"}))
        self.assertNotIn(
            "resilience",
            get_context_tags({"tool_name": "Bash", "command": "debug SECRET_SENTINEL"}),
        )

    def test_compact_payload_rejects_controls_and_over_budget_content(self) -> None:
        unsafe = {"text": "Do not ring\x07", "author": "Author", "book": "Book"}
        with self.assertRaises(ValueError):
            format_quote_message(unsafe)
        bidi = {"text": "safe\u202eevil", "author": "Author", "book": "Book"}
        with self.assertRaises(ValueError):
            format_quote_message(bidi)
        oversized = {"text": "界" * 200, "author": "Author", "book": "Book"}
        with self.assertRaises(ValueError):
            format_quote_message(oversized)


if __name__ == "__main__":
    unittest.main()
