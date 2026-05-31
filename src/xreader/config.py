from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class TwikitConfig:
    """Credentials and local Twikit settings loaded from the environment."""

    username: str | None
    email: str | None
    password: str | None
    totp_secret: str | None
    cookies_file: Path
    impersonate: str | None
    cookie_only: bool = False
    enable_ui_metrics: bool = True
    language: str = "en-US"


class ConfigError(ValueError):
    """Raised when required environment configuration is missing."""


def load_config(env_file: Path | None = Path(".env"), cookies_file: Path | None = None, language: str | None = None) -> TwikitConfig:
    """Load Twikit settings from .env and process environment variables."""

    if env_file is not None and env_file.exists():
        load_dotenv(env_file)

    configured_cookies_file = cookies_file or Path(os.getenv("TWIKIT_COOKIES_FILE", ".cache/twikit/cookies.json"))
    cookie_only = _bool_env("TWIKIT_COOKIE_ONLY", default=False)
    username = _optional_env("TWIKIT_USERNAME") if cookie_only else _required_env("TWIKIT_USERNAME")
    password = _optional_env("TWIKIT_PASSWORD") if cookie_only else _required_env("TWIKIT_PASSWORD")

    return TwikitConfig(
        username=username,
        email=_optional_env("TWIKIT_EMAIL"),
        password=password,
        totp_secret=_optional_env("TWIKIT_TOTP_SECRET"),
        cookies_file=configured_cookies_file,
        impersonate=_optional_env("TWIKIT_IMPERSONATE"),
        cookie_only=cookie_only,
        enable_ui_metrics=_bool_env("TWIKIT_ENABLE_UI_METRICS", default=True),
        language=language or os.getenv("TWIKIT_LANGUAGE", "en-US"),
    )


def _required_env(name: str) -> str:
    value = _optional_env(name)
    if value is None:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _bool_env(name: str, *, default: bool) -> bool:
    value = _optional_env(name)
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no", "off"}
