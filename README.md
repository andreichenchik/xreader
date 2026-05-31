# xreader

Minimal `twikit`-based CLI for exporting a small batch of tweets from your X timeline.

## Setup

Dependencies and Python are pinned in `pyproject.toml` and `uv.lock`.

```bash
uv sync
cp .env.example .env
```

Fill `.env` with your account credentials. Runtime cookies are saved to `.cache/twikit/cookies.json` by default and are ignored by git.

## Usage

Fetch the default Following timeline as readable text:

```bash
uv run xreader --count 20
```

Fetch For You and output JSON Lines:

```bash
uv run xreader --timeline for-you --format jsonl --count 20
```

## Configuration

Required environment variables:

- `TWIKIT_USERNAME`
- `TWIKIT_PASSWORD`

Optional environment variables:

- `TWIKIT_EMAIL`
- `TWIKIT_TOTP_SECRET`
- `TWIKIT_COOKIES_FILE` defaults to `.cache/twikit/cookies.json`
- `TWIKIT_LANGUAGE` defaults to `en-US`

## Development

```bash
uv run python -m unittest discover -s tests
```
