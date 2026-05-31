from __future__ import annotations

import unittest

from xreader.models import TweetSummary


class FakeUser:
    name = "Example User"
    screen_name = "example"


class FakeTweet:
    id = "12345"
    user = FakeUser()
    created_at = "Mon Jan 01 00:00:00 +0000 2024"
    full_text = "Hello from Twikit"
    reply_count = 1
    retweet_count = 2
    favorite_count = 3
    view_count = "4"
    retweeted_tweet = None


class TweetSummaryTests(unittest.TestCase):
    def test_builds_persistence_friendly_summary_from_twikit_tweet(self) -> None:
        summary = TweetSummary.from_twikit(FakeTweet())

        self.assertEqual(summary.id, "12345")
        self.assertEqual(summary.author_name, "Example User")
        self.assertEqual(summary.author_screen_name, "example")
        self.assertEqual(summary.text, "Hello from Twikit")
        self.assertEqual(summary.url, "https://x.com/example/status/12345")
        self.assertEqual(summary.view_count, 4)

    def test_falls_back_to_web_status_url_without_screen_name(self) -> None:
        class TweetWithoutUser:
            id = "67890"
            user = None
            text = "No user attached"

        summary = TweetSummary.from_twikit(TweetWithoutUser())

        self.assertEqual(summary.url, "https://x.com/i/web/status/67890")
        self.assertEqual(summary.text, "No user attached")

    def test_uses_original_tweet_text_for_retweets(self) -> None:
        class Retweeter:
            name = "Retweeter"
            screen_name = "retweeter"

        class OriginalUser:
            name = "Original User"
            screen_name = "original"

        class OriginalTweet:
            id = "999"
            user = OriginalUser()
            created_at = "Tue Jan 02 00:00:00 +0000 2024"
            full_text = "Full original tweet text without truncation"
            reply_count = 4
            retweet_count = 5
            favorite_count = 6
            view_count = 7

        class Retweet:
            id = "123"
            user = Retweeter()
            full_text = "RT @original: Full original tweet text…"
            retweeted_tweet = OriginalTweet()

        summary = TweetSummary.from_twikit(Retweet())

        self.assertEqual(summary.id, "999")
        self.assertEqual(summary.author_screen_name, "original")
        self.assertEqual(summary.text, "Full original tweet text without truncation")
        self.assertEqual(summary.url, "https://x.com/original/status/999")
        self.assertEqual(summary.retweeted_by_screen_name, "retweeter")
        self.assertEqual(summary.retweeted_by_name, "Retweeter")


if __name__ == "__main__":
    unittest.main()
