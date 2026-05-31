from __future__ import annotations

import json
import textwrap
from collections.abc import Iterable

from xreader.models import TweetSummary


def format_human(tweets: Iterable[TweetSummary]) -> str:
    """Format tweets as readable terminal text."""

    items = list(tweets)
    if not items:
        return "No tweets returned."

    blocks = [_format_human_tweet(index, tweet) for index, tweet in enumerate(items, start=1)]
    return "\n\n".join(blocks)


def format_jsonl(tweets: Iterable[TweetSummary]) -> str:
    """Format tweets as newline-delimited JSON objects."""

    return "\n".join(json.dumps(tweet.to_dict(), ensure_ascii=False) for tweet in tweets)


def _format_human_tweet(index: int, tweet: TweetSummary) -> str:
    author = _format_author(tweet)
    created_at = f" · {tweet.created_at}" if tweet.created_at else ""
    retweeted_by = _format_retweeted_by(tweet)
    metrics = _format_metrics(tweet)
    body = textwrap.indent(tweet.text.strip() or "(empty text)", "  ")

    lines = [f"{index}. {author}{created_at}{retweeted_by}", body, f"  {tweet.url}"]
    if metrics:
        lines.append(f"  {metrics}")
    return "\n".join(lines)


def _format_author(tweet: TweetSummary) -> str:
    if tweet.author_screen_name and tweet.author_name:
        return f"@{tweet.author_screen_name} ({tweet.author_name})"
    if tweet.author_screen_name:
        return f"@{tweet.author_screen_name}"
    if tweet.author_name:
        return tweet.author_name
    return "Unknown author"


def _format_retweeted_by(tweet: TweetSummary) -> str:
    if tweet.retweeted_by_screen_name and tweet.retweeted_by_name:
        return f" · retweeted by @{tweet.retweeted_by_screen_name} ({tweet.retweeted_by_name})"
    if tweet.retweeted_by_screen_name:
        return f" · retweeted by @{tweet.retweeted_by_screen_name}"
    if tweet.retweeted_by_name:
        return f" · retweeted by {tweet.retweeted_by_name}"
    return ""


def _format_metrics(tweet: TweetSummary) -> str:
    metrics = [
        ("replies", tweet.reply_count),
        ("retweets", tweet.retweet_count),
        ("likes", tweet.favorite_count),
        ("views", tweet.view_count),
    ]
    return " · ".join(f"{name}: {value}" for name, value in metrics if value is not None)
