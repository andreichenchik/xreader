from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Protocol

from twikit import Client

from xreader.config import TwikitConfig
from xreader.models import TweetSummary

Timeline = Literal["following", "for-you"]


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
        if timeline == "following":
            return await self._client.get_latest_timeline(count=count)
        if timeline == "for-you":
            return await self._client.get_timeline(count=count)
        raise ValueError(f"Unsupported timeline: {timeline}")


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

    return summaries


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
