from __future__ import annotations

import unittest

from xreader.feed import _collect_summaries


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
