from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xreader.config import ConfigError, load_config


class LoadConfigTests(unittest.TestCase):
    def test_loads_required_and_optional_values_from_environment(self) -> None:
        env = {
            "TWIKIT_USERNAME": "andrei",
            "TWIKIT_EMAIL": "andrei@example.com",
            "TWIKIT_PASSWORD": "secret",
            "TWIKIT_TOTP_SECRET": "totp",
            "TWIKIT_COOKIES_FILE": ".cache/custom.json",
            "TWIKIT_LANGUAGE": "ru-RU",
            "TWIKIT_IMPERSONATE": "chrome124",
            "TWIKIT_ENABLE_UI_METRICS": "false",
            "TWIKIT_COOKIE_ONLY": "true",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_config(env_file=None)

        self.assertEqual(config.username, "andrei")
        self.assertEqual(config.email, "andrei@example.com")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.totp_secret, "totp")
        self.assertEqual(config.cookies_file, Path(".cache/custom.json"))
        self.assertEqual(config.impersonate, "chrome124")
        self.assertTrue(config.cookie_only)
        self.assertFalse(config.enable_ui_metrics)
        self.assertEqual(config.language, "ru-RU")

    def test_defaults_ui_metrics_to_enabled(self) -> None:
        env = {
            "TWIKIT_USERNAME": "andrei",
            "TWIKIT_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_config(env_file=None)

        self.assertTrue(config.enable_ui_metrics)

    def test_cookie_only_does_not_require_credentials(self) -> None:
        env = {
            "TWIKIT_COOKIE_ONLY": "true",
            "TWIKIT_COOKIES_FILE": "cookies.json",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_config(env_file=None)

        self.assertIsNone(config.username)
        self.assertIsNone(config.password)
        self.assertTrue(config.cookie_only)
        self.assertEqual(config.cookies_file, Path("cookies.json"))

    def test_cli_overrides_cookie_file_and_language(self) -> None:
        env = {
            "TWIKIT_USERNAME": "andrei",
            "TWIKIT_PASSWORD": "secret",
            "TWIKIT_COOKIES_FILE": ".cache/from-env.json",
            "TWIKIT_LANGUAGE": "en-US",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_config(env_file=None, cookies_file=Path("cookies.json"), language="ja-JP")

        self.assertEqual(config.cookies_file, Path("cookies.json"))
        self.assertEqual(config.language, "ja-JP")

    def test_loads_dotenv_file_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("TWIKIT_USERNAME=from_file\nTWIKIT_PASSWORD=secret\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(env_file=env_file)

        self.assertEqual(config.username, "from_file")
        self.assertEqual(config.password, "secret")

    def test_missing_required_values_raise_config_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigError, "TWIKIT_USERNAME"):
                load_config(env_file=None)


if __name__ == "__main__":
    unittest.main()
