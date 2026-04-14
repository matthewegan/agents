"""hscli command surface.

Design: JSON to stdout, errors to stderr, stable exit codes, a `raw` escape
hatch for any endpoint, and auto-pagination by default.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Optional

import click
import typer

from .client import BASE_URL, Client
from .config import load_config
from .errors import HSError, ValidationError
from .output import emit_error, emit_json, emit_raw

app = typer.Typer(
    name="hscli",
    help=(
        "Agent-friendly CLI for HubSpot CMS. JSON output, stable exit "
        "codes, raw passthrough for unwrapped endpoints."
    ),
    no_args_is_help=True,
    add_completion=False,
)

auth_app = typer.Typer(help="Auth and credential checks.", no_args_is_help=True)
cms_app = typer.Typer(help="CMS commands.", no_args_is_help=True)
landing_pages_app = typer.Typer(help="Landing page commands.", no_args_is_help=True)
site_pages_app = typer.Typer(help="Site page commands.", no_args_is_help=True)

app.add_typer(auth_app, name="auth")
app.add_typer(cms_app, name="cms")
cms_app.add_typer(landing_pages_app, name="landing-pages")
cms_app.add_typer(site_pages_app, name="site-pages")


# ---------- helpers ----------

def _client() -> Client:
    return Client(load_config())


def _parse_query(items: list[str]) -> Optional[dict]:
    if not items:
        return None
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValidationError(f"--query expects KEY=VALUE, got: {item!r}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def _load_data(data_arg: Optional[str]) -> Optional[dict]:
    if data_arg is None:
        return None
    if data_arg.startswith("@"):
        text = Path(data_arg[1:]).read_text()
    else:
        text = data_arg
    try:
        return _json.loads(text)
    except _json.JSONDecodeError as e:
        raise ValidationError(f"--data is not valid JSON: {e}")


def _find_modules_in_layout(layout_sections: dict, target: str) -> list[str]:
    """Walk layoutSections recursively to find module paths matching target."""
    matches = []

    def _walk(obj: object) -> None:
        if isinstance(obj, dict):
            path = obj.get("path")
            if isinstance(path, str) and target.lower() in path.lower():
                matches.append(path)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(layout_sections)
    return matches


# ---------- auth ----------

@auth_app.command("check")
def auth_check() -> None:
    """Verify credentials by calling the account info endpoint."""
    with _client() as c:
        data = c.get_json("/account-info/v3/api-usage/daily/private-apps")
    emit_json({"ok": True, "usage": data})


# ---------- raw / paginate ----------

@app.command("raw")
def raw(
    method: str = typer.Argument(..., help="HTTP method: GET/POST/PUT/PATCH/DELETE"),
    path: str = typer.Argument(..., help="API path, e.g. /cms/v3/pages/landing-pages"),
    query: list[str] = typer.Option(
        [], "--query", "-q", help="KEY=VALUE query param (repeatable)"
    ),
    data: Optional[str] = typer.Option(
        None, "--data", "-d", help="JSON body string, or @path/to/file.json"
    ),
) -> None:
    """Make a raw authenticated request. Escape hatch for any endpoint."""
    params = _parse_query(query)
    body = _load_data(data)

    with _client() as c:
        resp = c.request(method.upper(), path, params=params, json=body)

    if resp.status_code == 204 or not resp.content:
        emit_json({"ok": True, "status": resp.status_code})
        return
    try:
        parsed = resp.json()
    except _json.JSONDecodeError:
        emit_raw(resp.text)
    else:
        emit_json(parsed)


@app.command("paginate")
def paginate(
    path: str = typer.Argument(..., help="Paginated API path"),
    query: list[str] = typer.Option([], "--query", "-q"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Max items to return"),
) -> None:
    """Follow pagination cursors and emit a JSON array of all results."""
    params = _parse_query(query)
    with _client() as c:
        items = list(c.paginate(path, params=params, limit=limit))
    emit_json(items)


# ---------- cms / landing-pages ----------

@landing_pages_app.command("list")
def landing_pages_list(
    state: Optional[str] = typer.Option(
        None, "--state", help="Filter by state, e.g. PUBLISHED, DRAFT"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", help="Filter by name (contains, case-insensitive)"
    ),
    limit: Optional[int] = typer.Option(None, "--limit"),
    query: list[str] = typer.Option(
        [], "--query", "-q", help="Additional KEY=VALUE query params (repeatable)"
    ),
) -> None:
    """List landing pages with optional filters."""
    params = _parse_query(query) or {}
    if state:
        params["state"] = state.upper()
    if name:
        params["name__icontains"] = name

    with _client() as c:
        items = list(
            c.paginate("/cms/v3/pages/landing-pages", params=params, limit=limit)
        )
    emit_json(items)


@landing_pages_app.command("get")
def landing_pages_get(
    page_id: str = typer.Argument(..., help="Landing page ID"),
) -> None:
    """Get full details of a single landing page."""
    with _client() as c:
        emit_json(c.get_json(f"/cms/v3/pages/landing-pages/{page_id}"))


@landing_pages_app.command("find-by-module")
def landing_pages_find_by_module(
    module: str = typer.Argument(
        ..., help="Module path or substring to search for in layoutSections"
    ),
    state: Optional[str] = typer.Option(
        None, "--state", help="Filter by state, e.g. PUBLISHED, DRAFT"
    ),
    scan_limit: Optional[int] = typer.Option(
        None, "--scan-limit", help="Max pages to scan from the API"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Max matching results to return"
    ),
) -> None:
    """Find landing pages that use a specific module.

    Fetches landing pages and inspects their layoutSections for modules
    whose path contains the given string (case-insensitive).
    """
    params: dict[str, str] = {}
    if state:
        params["state"] = state.upper()

    matches = []
    with _client() as c:
        for page in c.paginate(
            "/cms/v3/pages/landing-pages", params=params, limit=scan_limit
        ):
            layout = page.get("layoutSections", {})
            found_modules = _find_modules_in_layout(layout, module)
            if found_modules:
                matches.append({
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "slug": page.get("slug"),
                    "state": page.get("state"),
                    "url": page.get("url"),
                    "updatedAt": page.get("updatedAt"),
                    "matched_modules": found_modules,
                })
                if limit is not None and len(matches) >= limit:
                    break

    emit_json(matches)


# ---------- cms / site-pages ----------

@site_pages_app.command("list")
def site_pages_list(
    state: Optional[str] = typer.Option(
        None, "--state", help="Filter by state, e.g. PUBLISHED, DRAFT"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", help="Filter by name (contains, case-insensitive)"
    ),
    limit: Optional[int] = typer.Option(None, "--limit"),
    query: list[str] = typer.Option(
        [], "--query", "-q", help="Additional KEY=VALUE query params (repeatable)"
    ),
) -> None:
    """List site pages with optional filters."""
    params = _parse_query(query) or {}
    if state:
        params["state"] = state.upper()
    if name:
        params["name__icontains"] = name

    with _client() as c:
        items = list(
            c.paginate("/cms/v3/pages/site-pages", params=params, limit=limit)
        )
    emit_json(items)


@site_pages_app.command("get")
def site_pages_get(
    page_id: str = typer.Argument(..., help="Site page ID"),
) -> None:
    """Get full details of a single site page."""
    with _client() as c:
        emit_json(c.get_json(f"/cms/v3/pages/site-pages/{page_id}"))


@site_pages_app.command("find-by-module")
def site_pages_find_by_module(
    module: str = typer.Argument(
        ..., help="Module path or substring to search for in layoutSections"
    ),
    state: Optional[str] = typer.Option(
        None, "--state", help="Filter by state, e.g. PUBLISHED, DRAFT"
    ),
    scan_limit: Optional[int] = typer.Option(
        None, "--scan-limit", help="Max pages to scan from the API"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Max matching results to return"
    ),
) -> None:
    """Find site pages that use a specific module.

    Fetches site pages and inspects their layoutSections for modules
    whose path contains the given string (case-insensitive).
    """
    params: dict[str, str] = {}
    if state:
        params["state"] = state.upper()

    matches = []
    with _client() as c:
        for page in c.paginate(
            "/cms/v3/pages/site-pages", params=params, limit=scan_limit
        ):
            layout = page.get("layoutSections", {})
            found_modules = _find_modules_in_layout(layout, module)
            if found_modules:
                matches.append({
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "slug": page.get("slug"),
                    "state": page.get("state"),
                    "url": page.get("url"),
                    "updatedAt": page.get("updatedAt"),
                    "matched_modules": found_modules,
                })
                if limit is not None and len(matches) >= limit:
                    break

    emit_json(matches)


# ---------- entry point ----------

def main() -> None:
    try:
        app(standalone_mode=False)
    except click.exceptions.Abort:
        sys.exit(130)
    except click.exceptions.UsageError as e:
        e.show()
        sys.exit(2)
    except click.exceptions.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except HSError as e:
        emit_error(str(e))
        sys.exit(e.exit_code)
    except Exception as e:
        emit_error(f"unexpected: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
