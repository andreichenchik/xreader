from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class TwikitConfig:
    """Credentials and local Twikit settings loaded from the environment."""

    username: str
    email: str | None
    password: str
    totp_secret: str | None
    cookies_file: Path
    language: str = "en-US"


class ConfigError(ValueError):
    """Raised when required environment configuration is missing."""


def load_config(env_file: Path | None = Path(".env"), cookies_file: Path | None = None, language: str | None = None) -> TwikitConfig:
    """Load Twikit settings from .env and process environment variables."""

    if env_file is not None and env_file.exists():
        load_dotenv(env_file)

    username = _required_env("TWIKIT_USERNAME")
    password = _required_env("TWIKIT_PASSWORD")
    configured_cookies_file = cookies_file or Path(os.getenv("TWIKIT_COOKIES_FILE", ".cache/twikit/cookies.json"))

    return TwikitConfig(
        username=username,
        email=_optional_env("TWIKIT_EMAIL"),
        password=password,
        totp_secret=_optional_env("TWIKIT_TOTP_SECRET"),
        cookies_file=configured_cookies_file,
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
