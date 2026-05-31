from __future__ import annotations

import json
import unittest

from xreader.formatters import format_human, format_jsonl
from xreader.models import TweetSummary


class FormatterTests(unittest.TestCase):
    def test_formats_human_readable_tweets(self) -> None:
        text = format_human([
            TweetSummary(
                id="123",
                author_name="Example User",
                author_screen_name="example",
                created_at="Mon Jan 01 00:00:00 +0000 2024",
                text="Hello\nworld",
                url="https://x.com/example/status/123",
                reply_count=1,
                retweet_count=2,
                favorite_count=3,
                view_count=4,
            )
        ])

        self.assertIn("1. @example (Example User)", text)
        self.assertIn("  Hello\n  world", text)
        self.assertIn("replies: 1 · retweets: 2 · likes: 3 · views: 4", text)

    def test_formats_empty_human_result(self) -> None:
        self.assertEqual(format_human([]), "No tweets returned.")

    def test_formats_jsonl(self) -> None:
        text = format_jsonl([
            TweetSummary(
                id="123",
                author_name="Example User",
                author_screen_name="example",
                created_at=None,
                text="Привет",
                url="https://x.com/example/status/123",
            )
        ])

        decoded = json.loads(text)
        self.assertEqual(decoded["id"], "123")
        self.assertEqual(decoded["text"], "Привет")


if __name__ == "__main__":
    unittest.main()
