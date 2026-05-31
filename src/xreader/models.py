from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TweetSummary:
    """Small, persistence-friendly representation of a tweet from a timeline."""

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
    retweeted_by_name: str | None = None
    retweeted_by_screen_name: str | None = None

    @classmethod
    def from_twikit(cls, tweet: Any) -> TweetSummary:
        """Create a summary from a Twikit Tweet-like object."""

        source_tweet = _source_tweet(tweet)
        tweet_id = str(getattr(source_tweet, "id"))
        user = getattr(source_tweet, "user", None)
        screen_name = _as_optional_str(getattr(user, "screen_name", None))
        retweeter = getattr(tweet, "user", None) if source_tweet is not tweet else None

        return cls(
            id=tweet_id,
            author_name=_as_optional_str(getattr(user, "name", None)),
            author_screen_name=screen_name,
            created_at=_as_optional_str(getattr(source_tweet, "created_at", None)),
            text=str(getattr(source_tweet, "full_text", None) or getattr(source_tweet, "text", "")),
            url=_tweet_url(tweet_id, screen_name),
            reply_count=_as_optional_int(getattr(source_tweet, "reply_count", None)),
            retweet_count=_as_optional_int(getattr(source_tweet, "retweet_count", None)),
            favorite_count=_as_optional_int(getattr(source_tweet, "favorite_count", None)),
            view_count=_as_optional_int(getattr(source_tweet, "view_count", None)),
            retweeted_by_name=_as_optional_str(getattr(retweeter, "name", None)),
            retweeted_by_screen_name=_as_optional_str(getattr(retweeter, "screen_name", None)),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary for persistence or JSONL output."""

        return asdict(self)


def _source_tweet(tweet: Any) -> Any:
    retweeted_tweet = getattr(tweet, "retweeted_tweet", None)
    return retweeted_tweet or tweet


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
