"""Credential loading.

Priority: environment variables, then ~/.config/bbcli/config.toml.
Never prompts — agents need deterministic, non-interactive behavior.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError

CONFIG_PATH = Path.home() / ".config" / "bbcli" / "config.toml"


@dataclass(frozen=True)
class Config:
    email: str
    api_token: str


def load_config() -> Config:
    email = os.environ.get("BITBUCKET_EMAIL")
    token = os.environ.get("BITBUCKET_API_TOKEN")

    if (not email or not token) and CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as f:
            data = tomllib.load(f)
        email = email or data.get("email")
        token = token or data.get("api_token")

    if not email or not token:
        raise ConfigError(
            "missing credentials: set BITBUCKET_EMAIL and BITBUCKET_API_TOKEN, "
            f"or create {CONFIG_PATH} with `email` and `api_token` fields"
        )

    return Config(email=email, api_token=token)
