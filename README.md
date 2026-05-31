# xreader

Minimal `twikit`-based CLI for exporting a small batch of tweets from your X timeline.

## Setup

Dependencies and Python are pinned in `pyproject.toml` and `uv.lock`.

```bash
uv sync
cp .env.example .env
```

Fill `.env` with your account credentials. Runtime cookies are saved to `.cache/twikit/cookies.json` by default and are ignored by git.

To bypass the password login flow, set `TWIKIT_COOKIE_ONLY=true` and point `TWIKIT_COOKIES_FILE` to an existing JSON cookies file. The file can be Twikit's saved cookie object or a browser-exported JSON list with `name`/`value` entries.

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

Required environment variables unless `TWIKIT_COOKIE_ONLY=true`:

- `TWIKIT_USERNAME`
- `TWIKIT_PASSWORD`

Optional environment variables:

- `TWIKIT_EMAIL`
- `TWIKIT_TOTP_SECRET`
- `TWIKIT_COOKIE_ONLY` defaults to `false`; set `true` to skip password login and load cookies directly
- `TWIKIT_COOKIES_FILE` defaults to `.cache/twikit/cookies.json`
- `TWIKIT_LANGUAGE` defaults to `en-US`
- `TWIKIT_IMPERSONATE` optional browser TLS fingerprint for Cloudflare/X 403s, e.g. `chrome124`
- `TWIKIT_ENABLE_UI_METRICS` defaults to `true`; set `false` if login fails while solving X `ui_metrics` JavaScript

## Development

```bash
uv run python -m unittest discover -s tests
```
