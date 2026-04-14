from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

from .errors import AuthError, ConfigError

HS_CLI_CONFIG_PATH = Path.home() / ".hscli" / "config.yml"
TOKEN_REFRESH_URL = "https://api.hubapi.com/localdevauth/v1/auth/refresh"


@dataclass(frozen=True)
class Config:
    access_token: str


def _refresh_access_token(personal_access_key: str) -> str:
    """Exchange a personal access key for a short-lived access token."""
    try:
        resp = httpx.post(
            TOKEN_REFRESH_URL,
            json={"encodedOAuthRefreshToken": personal_access_key},
            headers={"User-Agent": "hscli/0.1"},
            timeout=15.0,
        )
    except httpx.HTTPError as e:
        raise AuthError(f"failed to refresh access token: {e}") from e

    if resp.status_code >= 400:
        raise AuthError(
            f"token refresh failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        data = resp.json()
    except ValueError as e:
        raise AuthError(f"invalid response from token refresh: {resp.text[:200]}") from e

    token = data.get("oauthAccessToken") or data.get("access_token")
    if not token:
        raise AuthError(f"no access token in refresh response: {data}")
    return token


def _load_from_hs_cli() -> str | None:
    """Read personal access key from the HubSpot CLI config (~/.hscli/config.yml).

    If a cached access token exists and hasn't expired, use it directly.
    Otherwise, exchange the personal access key for a fresh token.
    """
    if not HS_CLI_CONFIG_PATH.exists():
        return None

    try:
        raw = HS_CLI_CONFIG_PATH.read_text()
        data: Any = yaml.safe_load(raw)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    default_id = data.get("defaultAccount")
    accounts = data.get("accounts", [])
    if not accounts:
        return None

    account = None
    for acct in accounts:
        if acct.get("accountId") == default_id:
            account = acct
            break
    if account is None:
        account = accounts[0]

    # Check for a cached access token that hasn't expired
    token_info = account.get("auth", {}).get("tokenInfo", {})
    cached_token = token_info.get("accessToken")
    expires_at = token_info.get("expiresAt")
    if cached_token and expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at)
            if expiry > datetime.now(timezone.utc):
                return cached_token
        except (ValueError, TypeError):
            pass

    pak = account.get("personalAccessKey")
    if not pak:
        return None

    return _refresh_access_token(pak)


def load_config() -> Config:
    # 1. Environment variable (highest priority)
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")

    # 2. HubSpot CLI config (personal access key → access token exchange)
    if not token:
        token = _load_from_hs_cli()

    if not token:
        raise ConfigError(
            "missing credentials: set HUBSPOT_ACCESS_TOKEN "
            "or authenticate the HubSpot CLI with `hs account auth`"
        )

    return Config(access_token=token)
