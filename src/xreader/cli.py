from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TextIO

from xreader.config import ConfigError, load_config
from xreader.feed import Timeline, TwikitTweetFeed
from xreader.formatters import format_human, format_jsonl

OutputFormat = str


def main(argv: list[str] | None = None) -> int:
    """Run the xreader command line interface."""

    return asyncio.run(run(argv, sys.stdout, sys.stderr))


async def run(argv: list[str] | None, stdout: TextIO, stderr: TextIO) -> int:
    """Parse CLI arguments, fetch tweets, and write them to stdout."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(
            env_file=args.env_file,
            cookies_file=args.cookies_file,
            language=args.language,
        )
        feed = TwikitTweetFeed(config)
        tweets = await feed.fetch(timeline=args.timeline, count=args.count)
    except ConfigError as error:
        print(f"Configuration error: {error}", file=stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - CLI should return a readable failure instead of a traceback.
        print(f"Twikit feed export failed: {error}", file=stderr)
        return 1

    print(_format_output(tweets, args.output_format), file=stdout)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for tests and shell completion wrappers."""

    parser = argparse.ArgumentParser(description="Export a small batch of tweets from your Twikit timeline.")
    parser.add_argument("--count", type=_positive_int, default=20, help="number of tweets to fetch (default: 20)")
    parser.add_argument(
        "--timeline",
        choices=("following", "for-you"),
        default="following",
        help="timeline to fetch: following or for-you (default: following)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("human", "jsonl"),
        default="human",
        help="output format (default: human)",
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="dotenv file to load (default: .env)")
    parser.add_argument("--cookies-file", type=Path, help="override TWIKIT_COOKIES_FILE for this run")
    parser.add_argument("--language", help="override TWIKIT_LANGUAGE for this run")
    return parser


def _format_output(tweets: object, output_format: OutputFormat) -> str:
    if output_format == "human":
        return format_human(tweets)  # type: ignore[arg-type]
    if output_format == "jsonl":
        return format_jsonl(tweets)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported output format: {output_format}")


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
