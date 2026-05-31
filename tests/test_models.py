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


if __name__ == "__main__":
    unittest.main()
