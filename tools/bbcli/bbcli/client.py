"""HTTP client for the Bitbucket Cloud REST API.

Auth: HTTP Basic with Atlassian email + API token (per the Bitbucket docs).
Pagination: the API returns `{values: [...], next: "full-url"}` and we follow
`next` until exhausted.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional

import httpx

from .config import Config
from .errors import AuthError, BBError, NotFoundError, ValidationError

BASE_URL = "https://api.bitbucket.org/2.0"


class Client:
    def __init__(self, config: Config):
        self._client = httpx.Client(
            base_url=BASE_URL,
            auth=(config.email, config.api_token),
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "bbcli/0.1"},
            follow_redirects=True,
        )

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Any = None,
        accept: str = "application/json",
    ) -> httpx.Response:
        # Accept both relative paths ("/repositories") and absolute URLs
        # (needed when following a `next` cursor from a paginated response).
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = path if path.startswith("/") else "/" + path

        headers = {"Accept": accept}
        resp = self._client.request(
            method, url, params=params, json=json, headers=headers
        )
        _raise_for_status(resp)
        return resp

    def get_json(self, path: str, *, params: Optional[dict] = None) -> Any:
        return self.request("GET", path, params=params).json()

    def paginate(
        self,
        path: str,
        *,
        params: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[dict]:
        """Yield items from a paginated endpoint, following `next` links."""
        url: Optional[str] = path
        current_params = params
        count = 0
        while url:
            resp = self.request("GET", url, params=current_params)
            data = resp.json()
            for item in data.get("values", []):
                if limit is not None and count >= limit:
                    return
                yield item
                count += 1
            url = data.get("next")
            # `next` is a full URL that already has the query string baked in,
            # so we must not re-apply the original params on subsequent pages.
            current_params = None


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return

    try:
        body: Any = resp.json()
    except ValueError:
        body = resp.text

    msg = f"HTTP {resp.status_code} {resp.reason_phrase}: {body}"

    if resp.status_code in (401, 403):
        raise AuthError(msg)
    if resp.status_code == 404:
        raise NotFoundError(msg)
    if 400 <= resp.status_code < 500:
        raise ValidationError(msg)
    raise BBError(msg)
