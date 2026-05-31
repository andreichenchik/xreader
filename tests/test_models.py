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
    quote = None
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
        self.assertIsNone(summary.quoted_tweet)
        self.assertIsNone(summary.reposted_tweet)
        self.assertEqual(summary.thread_tweets, ())

    def test_falls_back_to_web_status_url_without_screen_name(self) -> None:
        class TweetWithoutUser:
            id = "67890"
            user = None
            text = "No user attached"

        summary = TweetSummary.from_twikit(TweetWithoutUser())

        self.assertEqual(summary.url, "https://x.com/i/web/status/67890")
        self.assertEqual(summary.text, "No user attached")

    def test_preserves_repost_context_without_replacing_outer_tweet(self) -> None:
        class Reposter:
            name = "Reposter"
            screen_name = "reposter"

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
            quote = None
            retweeted_tweet = None

        class Repost:
            id = "123"
            user = Reposter()
            created_at = "Tue Jan 02 01:00:00 +0000 2024"
            full_text = "RT @original: Full original tweet text…"
            reply_count = 0
            retweet_count = 0
            favorite_count = 0
            view_count = None
            quote = None
            retweeted_tweet = OriginalTweet()

        summary = TweetSummary.from_twikit(Repost())

        self.assertEqual(summary.id, "123")
        self.assertEqual(summary.author_screen_name, "reposter")
        self.assertEqual(summary.text, "RT @original: Full original tweet text…")
        self.assertIsNotNone(summary.reposted_tweet)
        assert summary.reposted_tweet is not None
        self.assertEqual(summary.reposted_tweet.id, "999")
        self.assertEqual(summary.reposted_tweet.author_screen_name, "original")
        self.assertEqual(summary.reposted_tweet.text, "Full original tweet text without truncation")
        self.assertEqual(summary.reposted_tweet.url, "https://x.com/original/status/999")

    def test_preserves_quoted_tweet_context(self) -> None:
        class QuotedUser:
            name = "Quoted User"
            screen_name = "quoted"

        class QuotedTweet:
            id = "222"
            user = QuotedUser()
            created_at = "Tue Jan 02 00:00:00 +0000 2024"
            full_text = "Quoted tweet text"
            reply_count = 10
            retweet_count = 11
            favorite_count = 12
            view_count = 13
            quote = None
            retweeted_tweet = None

        class QuoteTweet(FakeTweet):
            id = "111"
            full_text = "My comment on this"
            quote = QuotedTweet()

        summary = TweetSummary.from_twikit(QuoteTweet())

        self.assertEqual(summary.id, "111")
        self.assertEqual(summary.text, "My comment on this")
        self.assertIsNotNone(summary.quoted_tweet)
        assert summary.quoted_tweet is not None
        self.assertEqual(summary.quoted_tweet.id, "222")
        self.assertEqual(summary.quoted_tweet.author_screen_name, "quoted")
        self.assertEqual(summary.quoted_tweet.text, "Quoted tweet text")

    def test_preserves_thread_context_without_repeating_root_tweet(self) -> None:
        class ThreadUser:
            name = "Thread User"
            screen_name = "threader"

        class ThreadTweet:
            user = ThreadUser()
            reply_count = 0
            retweet_count = 0
            favorite_count = 0
            view_count = None
            quote = None
            retweeted_tweet = None
            thread = None

            def __init__(self, tweet_id: str, text: str, created_at: str) -> None:
                self.id = tweet_id
                self.full_text = text
                self.created_at = created_at

        root = ThreadTweet("1", "First tweet", "Mon Jan 01 00:00:00 +0000 2024")
        first_reply = ThreadTweet("2", "First reply", "Tue Jan 02 00:00:00 +0000 2024")
        second_reply = ThreadTweet("3", "Second reply", "Wed Jan 03 00:00:00 +0000 2024")
        root.thread = [root, first_reply, second_reply]

        summary = TweetSummary.from_twikit(root)

        self.assertEqual(summary.id, "1")
        self.assertEqual(summary.text, "First tweet")
        self.assertEqual([tweet.id for tweet in summary.thread_tweets], ["2", "3"])
        self.assertEqual([tweet.text for tweet in summary.thread_tweets], ["First reply", "Second reply"])


if __name__ == "__main__":
    unittest.main()
