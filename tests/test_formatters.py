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

    def test_formats_repost_as_original_tweet_with_repost_context(self) -> None:
        text = format_human([
            TweetSummary(
                id="123",
                author_name="Reposter",
                author_screen_name="reposter",
                created_at=None,
                text="RT @original: Full original text",
                url="https://x.com/reposter/status/123",
                reposted_tweet=TweetSummary(
                    id="999",
                    author_name="Original User",
                    author_screen_name="original",
                    created_at=None,
                    text="Full original text",
                    url="https://x.com/original/status/999",
                ),
            )
        ])

        self.assertIn("1. @original (Original User) · reposted by @reposter (Reposter)", text)
        self.assertIn("  Full original text", text)
        self.assertIn("  https://x.com/original/status/999", text)
        self.assertNotIn("RT @original", text)
        self.assertNotIn("https://x.com/reposter/status/123", text)

    def test_formats_quote_tweet_as_left_bordered_card(self) -> None:
        text = format_human([
            TweetSummary(
                id="111",
                author_name="Example User",
                author_screen_name="example",
                created_at=None,
                text="My comment on this",
                url="https://x.com/example/status/111",
                quoted_tweet=TweetSummary(
                    id="222",
                    author_name="Quoted User",
                    author_screen_name="quoted",
                    created_at=None,
                    text="Quoted tweet text",
                    url="https://x.com/quoted/status/222",
                ),
            )
        ])

        self.assertIn("  My comment on this", text)
        self.assertIn("  │ @quoted (Quoted User)", text)
        self.assertIn("  │ Quoted tweet text", text)
        self.assertIn("  │ https://x.com/quoted/status/222", text)
        self.assertLess(text.index("  My comment on this"), text.index("  │ @quoted (Quoted User)"))
        self.assertLess(text.index("  │ https://x.com/quoted/status/222"), text.index("  https://x.com/example/status/111"))

    def test_formats_thread_tweets_as_left_bordered_continuation(self) -> None:
        text = format_human([
            TweetSummary(
                id="111",
                author_name="Thread User",
                author_screen_name="threader",
                created_at="Mon Jan 01 00:00:00 +0000 2024",
                text="First tweet",
                url="https://x.com/threader/status/111",
                thread_tweets=(
                    TweetSummary(
                        id="222",
                        author_name="Thread User",
                        author_screen_name="threader",
                        created_at="Tue Jan 02 00:00:00 +0000 2024",
                        text="Second tweet",
                        url="https://x.com/threader/status/222",
                    ),
                    TweetSummary(
                        id="333",
                        author_name="Thread User",
                        author_screen_name="threader",
                        created_at="Wed Jan 03 00:00:00 +0000 2024",
                        text="Third tweet",
                        url="https://x.com/threader/status/333",
                    ),
                ),
            )
        ])

        self.assertIn("  First tweet", text)
        self.assertIn("  │ @threader (Thread User) · Tue Jan 02 00:00:00 +0000 2024", text)
        self.assertIn("  │ Second tweet", text)
        self.assertIn("  │ https://x.com/threader/status/222", text)
        self.assertIn("  │ @threader (Thread User) · Wed Jan 03 00:00:00 +0000 2024", text)
        self.assertIn("  │ Third tweet", text)
        self.assertLess(text.index("  First tweet"), text.index("  │ Second tweet"))
        self.assertLess(text.index("  │ Third tweet"), text.index("  https://x.com/threader/status/111"))

    def test_formats_empty_human_result(self) -> None:
        self.assertEqual(format_human([]), "No tweets returned.")

    def test_formats_jsonl_with_nested_context(self) -> None:
        text = format_jsonl([
            TweetSummary(
                id="123",
                author_name="Example User",
                author_screen_name="example",
                created_at=None,
                text="Привет",
                url="https://x.com/example/status/123",
                quoted_tweet=TweetSummary(
                    id="222",
                    author_name="Quoted User",
                    author_screen_name="quoted",
                    created_at=None,
                    text="Quoted tweet text",
                    url="https://x.com/quoted/status/222",
                ),
                reposted_tweet=TweetSummary(
                    id="999",
                    author_name="Original User",
                    author_screen_name="original",
                    created_at=None,
                    text="Original text",
                    url="https://x.com/original/status/999",
                ),
                thread_tweets=(
                    TweetSummary(
                        id="333",
                        author_name="Thread User",
                        author_screen_name="threader",
                        created_at=None,
                        text="Thread text",
                        url="https://x.com/threader/status/333",
                    ),
                ),
            )
        ])

        decoded = json.loads(text)
        self.assertEqual(decoded["id"], "123")
        self.assertEqual(decoded["text"], "Привет")
        self.assertEqual(decoded["quoted_tweet"]["id"], "222")
        self.assertEqual(decoded["reposted_tweet"]["id"], "999")
        self.assertEqual(decoded["thread_tweets"][0]["id"], "333")


if __name__ == "__main__":
    unittest.main()
