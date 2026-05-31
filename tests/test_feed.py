from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from xreader.config import TwikitConfig
from xreader.feed import TwikitTweetFeed, _collect_summaries, _tweets_from_entries


class FakeUser:
    name = "Example User"
    screen_name = "example"


class FakeTweet:
    user = FakeUser()
    created_at = "Mon Jan 01 00:00:00 +0000 2024"
    text = "fallback text"
    reply_count = 0
    retweet_count = 0
    favorite_count = 0
    view_count = None
    quote = None
    retweeted_tweet = None
    thread = None

    def __init__(self, tweet_id: str, text: str | None = None, created_at: str | None = None) -> None:
        self.id = tweet_id
        if text is not None:
            self.full_text = text
        if created_at is not None:
            self.created_at = created_at


class FakePage:
    def __init__(self, tweets: list[FakeTweet], next_page: FakePage | None = None) -> None:
        self._tweets = tweets
        self._next_page = next_page

    def __iter__(self):
        return iter(self._tweets)

    async def next(self) -> FakePage | None:
        return self._next_page


class TwikitTweetFeedTests(unittest.IsolatedAsyncioTestCase):
    def test_passes_impersonate_setting_to_client(self) -> None:
        config = TwikitConfig(
            username="andrei",
            email=None,
            password="secret",
            totp_secret=None,
            cookies_file=Path("cookies.json"),
            impersonate="chrome124",
            cookie_only=False,
            enable_ui_metrics=False,
        )

        with patch("xreader.feed.Client") as client:
            TwikitTweetFeed(config)

        client.assert_called_once_with("en-US", impersonate="chrome124")

    async def test_passes_ui_metrics_setting_to_login(self) -> None:
        config = TwikitConfig(
            username="andrei",
            email=None,
            password="secret",
            totp_secret=None,
            cookies_file=Path("cookies.json"),
            impersonate=None,
            cookie_only=False,
            enable_ui_metrics=False,
        )
        with patch("xreader.feed.Client") as client_class:
            client = client_class.return_value
            client.login = AsyncMock()
            feed = TwikitTweetFeed(config)

            await feed._login()

        client.login.assert_awaited_once_with(
            auth_info_1="andrei",
            auth_info_2=None,
            password="secret",
            totp_secret=None,
            cookies_file="cookies.json",
            enable_ui_metrics=False,
        )

    async def test_cookie_only_loads_cookie_file_without_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cookies_file = Path(directory) / "cookies.json"
            cookies_file.write_text(json.dumps({"auth_token": "token", "ct0": "csrf"}), encoding="utf-8")
            config = TwikitConfig(
                username=None,
                email=None,
                password=None,
                totp_secret=None,
                cookies_file=cookies_file,
                impersonate=None,
                cookie_only=True,
            )

            with patch("xreader.feed.Client") as client_class:
                client = client_class.return_value
                client.login = AsyncMock()
                feed = TwikitTweetFeed(config)

                await feed._login()

        client.set_cookies.assert_called_once_with({"auth_token": "token", "ct0": "csrf"})
        client.login.assert_not_awaited()

    async def test_cookie_only_accepts_browser_exported_cookie_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cookies_file = Path(directory) / "cookies.json"
            cookies_file.write_text(
                json.dumps([{"name": "auth_token", "value": "token"}, {"name": "ct0", "value": "csrf"}]),
                encoding="utf-8",
            )
            config = TwikitConfig(
                username=None,
                email=None,
                password=None,
                totp_secret=None,
                cookies_file=cookies_file,
                impersonate=None,
                cookie_only=True,
            )

            with patch("xreader.feed.Client") as client_class:
                client = client_class.return_value
                feed = TwikitTweetFeed(config)

                await feed._login()

        client.set_cookies.assert_called_once_with({"auth_token": "token", "ct0": "csrf"})


class TimelineEntryParsingTests(unittest.TestCase):
    def test_parses_timeline_tweet_entries(self) -> None:
        tweet = FakeTweet("1", "tweet")
        entries = [{"content": {"itemContent": {}}}, {"content": {"value": "cursor"}}]

        with patch("xreader.feed.tweet_from_data", return_value=tweet):
            tweets = _tweets_from_entries(object(), entries)  # type: ignore[arg-type]

        self.assertEqual(tweets, [tweet])

    def test_parses_timeline_modules_as_thread_blocks(self) -> None:
        root = FakeTweet("1", "thread root")
        reply = FakeTweet("2", "thread reply")
        entries = [{"content": {"items": [{"item": {"itemContent": {}}}, {"item": {"itemContent": {}}}]}}]

        with patch("xreader.feed.tweet_from_data", side_effect=[root, reply]):
            tweets = _tweets_from_entries(object(), entries)  # type: ignore[arg-type]

        self.assertEqual(tweets, [root])
        self.assertEqual(root.thread, [root, reply])


class CollectSummariesTests(unittest.IsolatedAsyncioTestCase):
    async def test_collects_until_count_across_pages(self) -> None:
        second = FakePage([FakeTweet("3", "third")])
        first = FakePage([FakeTweet("1", "first"), FakeTweet("2", "second")], second)

        summaries = await _collect_summaries(first, 3)

        self.assertEqual([summary.id for summary in summaries], ["1", "2", "3"])
        self.assertEqual([summary.text for summary in summaries], ["first", "second", "third"])

    async def test_skips_duplicates_and_stops_at_count(self) -> None:
        second = FakePage([FakeTweet("2", "duplicate"), FakeTweet("3", "third")])
        first = FakePage([FakeTweet("1", "first"), FakeTweet("2", "second")], second)

        summaries = await _collect_summaries(first, 2)

        self.assertEqual([summary.id for summary in summaries], ["1", "2"])

    async def test_sorts_summaries_by_created_at_descending(self) -> None:
        first = FakePage([
            FakeTweet("1", "old", "Mon Jan 01 00:00:00 +0000 2024"),
            FakeTweet("2", "new", "Wed Jan 03 00:00:00 +0000 2024"),
            FakeTweet("3", "middle", "Tue Jan 02 00:00:00 +0000 2024"),
        ])

        summaries = await _collect_summaries(first, 3)

        self.assertEqual([summary.id for summary in summaries], ["2", "3", "1"])

    async def test_keeps_unparseable_created_at_values_last_in_original_order(self) -> None:
        first = FakePage([
            FakeTweet("1", "missing", ""),
            FakeTweet("2", "new", "2024-01-03T00:00:00+00:00"),
            FakeTweet("3", "invalid", "not a date"),
        ])

        summaries = await _collect_summaries(first, 3)

        self.assertEqual([summary.id for summary in summaries], ["2", "1", "3"])

    async def test_sorts_thread_blocks_by_latest_thread_tweet(self) -> None:
        thread_root = FakeTweet("1", "thread root", "Mon Jan 01 00:00:00 +0000 2024")
        thread_reply = FakeTweet("3", "thread reply", "Fri Jan 05 00:00:00 +0000 2024")
        thread_root.thread = [thread_root, thread_reply]
        first = FakePage([
            thread_root,
            FakeTweet("2", "normal tweet", "Wed Jan 03 00:00:00 +0000 2024"),
        ])

        summaries = await _collect_summaries(first, 2)

        self.assertEqual([summary.id for summary in summaries], ["1", "2"])
        self.assertEqual([tweet.id for tweet in summaries[0].thread_tweets], ["3"])


if __name__ == "__main__":
    unittest.main()
