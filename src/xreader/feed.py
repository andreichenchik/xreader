from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import partial
from pathlib import Path
from typing import Any, Literal, Protocol

from twikit import Client
from twikit.tweet import tweet_from_data
from twikit.utils import Result, find_dict

from xreader.config import TwikitConfig
from xreader.models import TweetSummary

Timeline = Literal["following", "for-you"]

_MIN_CREATED_AT = datetime.min.replace(tzinfo=timezone.utc)


class TweetFeed(Protocol):
    """Source capable of returning tweet summaries from a timeline."""

    async def fetch(self, timeline: Timeline, count: int) -> list[TweetSummary]:
        """Return up to count tweets from the requested timeline."""


class TwikitTweetFeed:
    """TweetFeed implementation backed by an authenticated Twikit client."""

    def __init__(self, config: TwikitConfig) -> None:
        self._config = config
        self._client = Client(config.language, impersonate=config.impersonate)

    async def fetch(self, timeline: Timeline, count: int) -> list[TweetSummary]:
        """Login if needed, fetch timeline pages, and return tweet summaries."""

        if count <= 0:
            return []

        await self._login()

        first_page_count = min(count, 20)
        page = await self._fetch_page(timeline, first_page_count)
        return await _collect_summaries(page, count)

    async def _login(self) -> None:
        cookies_file = self._config.cookies_file
        _ensure_parent_directory(cookies_file)

        if self._config.cookie_only:
            _load_cookies_file(cookies_file, self._client)
            return

        if self._config.username is None or self._config.password is None:
            raise ValueError("Username and password are required unless TWIKIT_COOKIE_ONLY is enabled.")

        await self._client.login(
            auth_info_1=self._config.username,
            auth_info_2=self._config.email,
            password=self._config.password,
            totp_secret=self._config.totp_secret,
            cookies_file=str(cookies_file),
            enable_ui_metrics=self._config.enable_ui_metrics,
        )

    async def _fetch_page(self, timeline: Timeline, count: int) -> Any:
        return await _fetch_timeline_page(self._client, timeline, count)


async def _fetch_timeline_page(
    client: Client,
    timeline: Timeline,
    count: int,
    seen_tweet_ids: list[str] | None = None,
    cursor: str | None = None,
) -> Result[Any]:
    if timeline == "following":
        response, _ = await client.gql.home_latest_timeline(count, seen_tweet_ids, cursor)
    elif timeline == "for-you":
        response, _ = await client.gql.home_timeline(count, seen_tweet_ids, cursor)
    else:
        raise ValueError(f"Unsupported timeline: {timeline}")

    entries = _timeline_entries(response)
    next_cursor = _next_cursor(entries)
    fetch_next = None
    if next_cursor is not None:
        fetch_next = partial(_fetch_timeline_page, client, timeline, count, seen_tweet_ids, next_cursor)
    return Result(_tweets_from_entries(client, entries), fetch_next, next_cursor)


def _timeline_entries(response: dict[str, object]) -> list[dict[str, object]]:
    entries = find_dict(response, "entries", find_one=True)
    if not entries or not isinstance(entries[0], list):
        return []
    return [entry for entry in entries[0] if isinstance(entry, dict)]


def _next_cursor(entries: list[dict[str, object]]) -> str | None:
    for entry in reversed(entries):
        content = entry.get("content")
        if not isinstance(content, dict):
            continue
        value = content.get("value")
        if isinstance(value, str):
            return value
    return None


def _tweets_from_entries(client: Client, entries: list[dict[str, object]]) -> list[Any]:
    tweets = []
    for entry in entries:
        tweet = _tweet_from_timeline_item(client, entry)
        if tweet is not None:
            tweets.append(tweet)
            continue

        thread = _thread_from_timeline_module(client, entry)
        if thread:
            root = thread[0]
            root.thread = thread
            tweets.append(root)
    return tweets


def _tweet_from_timeline_item(client: Client, item: dict[str, object]) -> Any | None:
    if not _has_item_content(item):
        return None
    return tweet_from_data(client, item)


def _thread_from_timeline_module(client: Client, entry: dict[str, object]) -> list[Any]:
    content = entry.get("content")
    if not isinstance(content, dict):
        return []
    items = content.get("items")
    if not isinstance(items, list):
        return []

    tweets = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tweet = _tweet_from_timeline_item(client, item)
        if tweet is not None:
            tweets.append(tweet)
    return tweets


def _has_item_content(item: dict[str, object]) -> bool:
    content = item.get("content")
    if isinstance(content, dict) and "itemContent" in content:
        return True
    item_data = item.get("item")
    return isinstance(item_data, dict) and "itemContent" in item_data


async def _collect_summaries(page: Any, count: int) -> list[TweetSummary]:
    summaries: list[TweetSummary] = []
    current_page = page
    seen_ids: set[str] = set()

    while current_page is not None and len(summaries) < count:
        page_items = list(current_page)
        if not page_items:
            break

        added_from_page = 0
        for tweet in page_items:
            summary = TweetSummary.from_twikit(tweet)
            if summary.id in seen_ids:
                continue
            summaries.append(summary)
            seen_ids.add(summary.id)
            added_from_page += 1
            if len(summaries) >= count:
                break

        if len(summaries) >= count or added_from_page == 0:
            break

        next_page = getattr(current_page, "next", None)
        if next_page is None:
            break
        current_page = await next_page()

    return _sort_by_created_at_desc(summaries)


def _sort_by_created_at_desc(summaries: list[TweetSummary]) -> list[TweetSummary]:
    return sorted(summaries, key=_created_at_sort_key, reverse=True)


def _created_at_sort_key(summary: TweetSummary) -> tuple[int, datetime]:
    created_at = _timeline_created_at(summary)
    if created_at is None:
        return (0, _MIN_CREATED_AT)
    return (1, created_at)


def _timeline_created_at(summary: TweetSummary) -> datetime | None:
    parsed_dates = [_parse_created_at(summary.created_at)]
    if summary.reposted_tweet is None:
        parsed_dates.extend(_timeline_created_at(tweet) for tweet in summary.thread_tweets)
    return max((date for date in parsed_dates if date is not None), default=None)


def _parse_created_at(value: str | None) -> datetime | None:
    if value is None:
        return None

    parsed = _parse_twitter_created_at(value) or _parse_iso_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_twitter_created_at(value: str) -> datetime | None:
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_cookies_file(path: Path, client: Client) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Cookie-only mode requires an existing cookies file: {path}")

    with path.open(encoding="utf-8") as file:
        raw_cookies = json.load(file)

    if isinstance(raw_cookies, dict):
        client.set_cookies(raw_cookies)
        return

    if isinstance(raw_cookies, list):
        cookies = {
            cookie["name"]: cookie["value"]
            for cookie in raw_cookies
            if isinstance(cookie, dict) and "name" in cookie and "value" in cookie
        }
        if cookies:
            client.set_cookies(cookies)
            return

    raise ValueError("Cookies file must be a JSON object or a browser-exported list with name/value entries.")


def _ensure_parent_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
