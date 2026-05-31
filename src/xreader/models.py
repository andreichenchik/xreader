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

    @classmethod
    def from_twikit(cls, tweet: Any) -> TweetSummary:
        """Create a summary from a Twikit Tweet-like object."""

        tweet_id = str(getattr(tweet, "id"))
        user = getattr(tweet, "user", None)
        screen_name = _as_optional_str(getattr(user, "screen_name", None))

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
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary for persistence or JSONL output."""

        return asdict(self)


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
