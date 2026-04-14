"""HTTP client for the HubSpot API.

Auth: Bearer token, obtained automatically from the HubSpot CLI's personal
access key (~/.hscli/config.yml) or set explicitly via env/config.
Pagination: the API returns `{results: [...], paging: {next: {after: "cursor"}}}`
and we follow `after` cursors until exhausted.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional

import httpx

from .config import Config
from .errors import AuthError, HSError, NotFoundError, ValidationError

BASE_URL = "https://api.hubapi.com"
MAX_PAGES = 500


class Client:
    def __init__(self, config: Config):
        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {config.access_token}",
                "User-Agent": "hscli/0.1",
            },
            follow_redirects=True,
        )

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: object) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Any = None,
    ) -> httpx.Response:
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = path if path.startswith("/") else "/" + path

        try:
            resp = self._client.request(method, url, params=params, json=json)
        except httpx.TimeoutException:
            raise HSError(f"request timed out: {method} {url}")
        except httpx.ConnectError as e:
            raise HSError(f"cannot connect to HubSpot API ({url}): {e}")
        except httpx.HTTPError as e:
            raise HSError(f"network error during {method} {url}: {e}")

        _raise_for_status(resp)
        return resp

    def get_json(self, path: str, *, params: Optional[dict] = None) -> Any:
        resp = self.request("GET", path, params=params)
        try:
            return resp.json()
        except ValueError as e:
            raise HSError(
                f"expected JSON from {path}, got: {resp.text[:200]}"
            ) from e

    def paginate(
        self,
        path: str,
        *,
        params: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[dict]:
        """Yield items from a paginated endpoint, following `after` cursors.

        HubSpot uses cursor-based pagination with `paging.next.after`,
        not full-URL `next` links like Bitbucket.
        """
        current_params = dict(params) if params else {}
        count = 0
        seen_cursors: set[str] = set()
        page_count = 0
        while True:
            page_count += 1
            if page_count > MAX_PAGES:
                raise HSError(
                    f"pagination safety limit ({MAX_PAGES} pages) exceeded for {path}"
                )

            resp = self.request("GET", path, params=current_params)
            try:
                data = resp.json()
            except ValueError as e:
                raise HSError(
                    f"non-JSON response during pagination of {path} "
                    f"(after={current_params.get('after', 'initial')}): "
                    f"{resp.text[:200]}"
                ) from e

            if not isinstance(data, dict) or "results" not in data:
                raise HSError(
                    f"unexpected response shape from {path}: "
                    f"expected object with 'results' key, got: {str(data)[:200]}"
                )

            for item in data["results"]:
                if limit is not None and count >= limit:
                    return
                yield item
                count += 1

            paging = data.get("paging", {})
            next_page = paging.get("next", {})
            after = next_page.get("after")
            if not after:
                return
            if after in seen_cursors:
                raise HSError(
                    f"pagination cycle detected (cursor {after!r} seen twice)"
                )
            seen_cursors.add(after)
            current_params["after"] = after


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
    raise HSError(msg)
