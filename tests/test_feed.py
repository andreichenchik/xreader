from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from xreader.config import TwikitConfig
from xreader.feed import TwikitTweetFeed, _collect_summaries


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

    def __init__(self, tweet_id: str, text: str | None = None) -> None:
        self.id = tweet_id
        if text is not None:
            self.full_text = text


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


if __name__ == "__main__":
    unittest.main()
