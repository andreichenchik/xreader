from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

_MAX_NESTED_TWEET_DEPTH = 4


@dataclass(frozen=True)
class TweetSummary:
    """Display-friendly representation of a timeline tweet, including nested context."""

    id: str
    author_name: str | None
    author_screen_name: str | None
    created_at: str | None
    text: str
    url: str
    reply_count: int | None = None
    retweet_count: int | None = None
    favorite_count: int | None = None
    view_count: int | None = None
    quoted_tweet: TweetSummary | None = None
    reposted_tweet: TweetSummary | None = None
    thread_tweets: tuple[TweetSummary, ...] = ()

    @classmethod
    def from_twikit(cls, tweet: Any) -> TweetSummary:
        """Create a summary from a Twikit Tweet-like object while preserving quote, repost, and thread context."""

        return cls._from_twikit(tweet, depth=0, seen_ids=frozenset())

    @classmethod
    def _from_twikit(cls, tweet: Any, depth: int, seen_ids: frozenset[str]) -> TweetSummary:
        tweet_id = str(getattr(tweet, "id"))
        user = getattr(tweet, "user", None)
        screen_name = _as_optional_str(getattr(user, "screen_name", None))
        nested_seen_ids = seen_ids | frozenset({tweet_id})

        return cls(
            id=tweet_id,
            author_name=_as_optional_str(getattr(user, "name", None)),
            author_screen_name=screen_name,
            created_at=_as_optional_str(getattr(tweet, "created_at", None)),
            text=str(getattr(tweet, "full_text", None) or getattr(tweet, "text", "")),
            url=_tweet_url(tweet_id, screen_name),
            reply_count=_as_optional_int(getattr(tweet, "reply_count", None)),
            retweet_count=_as_optional_int(getattr(tweet, "retweet_count", None)),
            favorite_count=_as_optional_int(getattr(tweet, "favorite_count", None)),
            view_count=_as_optional_int(getattr(tweet, "view_count", None)),
            quoted_tweet=_nested_summary(getattr(tweet, "quote", None), depth, nested_seen_ids),
            reposted_tweet=_nested_summary(getattr(tweet, "retweeted_tweet", None), depth, nested_seen_ids),
            thread_tweets=_thread_summaries(tweet, depth, nested_seen_ids),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary for persistence or JSONL output."""

        return asdict(self)


def _nested_summary(tweet: Any, parent_depth: int, seen_ids: frozenset[str]) -> TweetSummary | None:
    if tweet is None or parent_depth >= _MAX_NESTED_TWEET_DEPTH:
        return None
    tweet_id = _tweet_id(tweet)
    if tweet_id is None or tweet_id in seen_ids:
        return None
    return TweetSummary._from_twikit(tweet, depth=parent_depth + 1, seen_ids=seen_ids)


def _thread_summaries(tweet: Any, parent_depth: int, seen_ids: frozenset[str]) -> tuple[TweetSummary, ...]:
    if parent_depth >= _MAX_NESTED_TWEET_DEPTH:
        return ()

    thread = getattr(tweet, "thread", None)
    if not thread:
        return ()

    summaries: list[TweetSummary] = []
    local_seen_ids = set(seen_ids)
    for thread_tweet in thread:
        tweet_id = _tweet_id(thread_tweet)
        if tweet_id is None or tweet_id in local_seen_ids:
            continue
        summary = TweetSummary._from_twikit(thread_tweet, depth=parent_depth + 1, seen_ids=frozenset(local_seen_ids))
        summaries.append(summary)
        local_seen_ids.add(summary.id)
    return tuple(summaries)


def _tweet_id(tweet: Any) -> str | None:
    return _as_optional_str(getattr(tweet, "id", None))


def _tweet_url(tweet_id: str, screen_name: str | None) -> str:
    if screen_name:
        return f"https://x.com/{screen_name}/status/{tweet_id}"
    return f"https://x.com/i/web/status/{tweet_id}"


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None


def _as_optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
