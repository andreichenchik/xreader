from __future__ import annotations

import json
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
    display_tweet = tweet.reposted_tweet or tweet
    reposted_by = _format_reposted_by(tweet) if tweet.reposted_tweet else ""
    metrics = _format_metrics(display_tweet)

    lines = [f"{index}. {_format_author(display_tweet)}{_format_created_at(display_tweet)}{reposted_by}"]
    lines.extend(_prefix_lines(_format_body_lines(display_tweet), "  "))
    lines.append(f"  {display_tweet.url}")
    if metrics:
        lines.append(f"  {metrics}")
    return "\n".join(lines)


def _format_body_lines(tweet: TweetSummary) -> list[str]:
    lines = _format_text_lines(tweet)
    if tweet.quoted_tweet is not None:
        lines.extend(_format_quote_block(tweet.quoted_tweet))
    lines.extend(_format_thread_blocks(tweet.thread_tweets))
    return lines


def _format_quote_block(tweet: TweetSummary) -> list[str]:
    return _prefix_lines(_format_card_lines(tweet), "│ ")


def _format_thread_blocks(tweets: tuple[TweetSummary, ...]) -> list[str]:
    lines: list[str] = []
    for tweet in tweets:
        if lines:
            lines.append("│")
        lines.extend(_prefix_lines(_format_card_lines(tweet), "│ "))
    return lines


def _format_card_lines(tweet: TweetSummary) -> list[str]:
    display_tweet = tweet.reposted_tweet or tweet
    reposted_by = _format_reposted_by(tweet) if tweet.reposted_tweet else ""
    metrics = _format_metrics(display_tweet)

    lines = [f"{_format_author(display_tweet)}{_format_created_at(display_tweet)}{reposted_by}"]
    lines.extend(_format_body_lines(display_tweet))
    lines.append(display_tweet.url)
    if metrics:
        lines.append(metrics)
    return lines


def _format_author(tweet: TweetSummary) -> str:
    if tweet.author_screen_name and tweet.author_name:
        return f"@{tweet.author_screen_name} ({tweet.author_name})"
    if tweet.author_screen_name:
        return f"@{tweet.author_screen_name}"
    if tweet.author_name:
        return tweet.author_name
    return "Unknown author"


def _format_created_at(tweet: TweetSummary) -> str:
    return f" · {tweet.created_at}" if tweet.created_at else ""


def _format_reposted_by(tweet: TweetSummary) -> str:
    if tweet.author_screen_name and tweet.author_name:
        return f" · reposted by @{tweet.author_screen_name} ({tweet.author_name})"
    if tweet.author_screen_name:
        return f" · reposted by @{tweet.author_screen_name}"
    if tweet.author_name:
        return f" · reposted by {tweet.author_name}"
    return " · reposted"


def _format_metrics(tweet: TweetSummary) -> str:
    metrics = [
        ("replies", tweet.reply_count),
        ("retweets", tweet.retweet_count),
        ("likes", tweet.favorite_count),
        ("views", tweet.view_count),
    ]
    return " · ".join(f"{name}: {value}" for name, value in metrics if value is not None)


def _format_text_lines(tweet: TweetSummary) -> list[str]:
    text = tweet.text.strip()
    return text.splitlines() if text else ["(empty text)"]


def _prefix_lines(lines: Iterable[str], prefix: str) -> list[str]:
    return [f"{prefix}{line}" for line in lines]
