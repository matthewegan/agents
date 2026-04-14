"""bbcli command surface.

Design: JSON to stdout, errors to stderr, stable exit codes, a `raw` escape
hatch for any endpoint we don't wrap, and auto-pagination by default.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import click
import typer

from .client import BASE_URL, Client
from .config import load_config
from .errors import BBError, ValidationError
from .output import emit_error, emit_json, emit_raw

app = typer.Typer(
    name="bb",
    help=(
        "Agent-friendly CLI for Bitbucket Cloud. JSON output, stable exit "
        "codes, raw passthrough for unwrapped endpoints."
    ),
    no_args_is_help=True,
    add_completion=False,
)

auth_app = typer.Typer(help="Auth and credential checks.", no_args_is_help=True)
repo_app = typer.Typer(help="Repository commands.", no_args_is_help=True)
pr_app = typer.Typer(help="Pull request commands.", no_args_is_help=True)
branch_app = typer.Typer(help="Branch commands.", no_args_is_help=True)
commit_app = typer.Typer(help="Commit commands.", no_args_is_help=True)
pipeline_app = typer.Typer(help="Pipeline commands.", no_args_is_help=True)

app.add_typer(auth_app, name="auth")
app.add_typer(repo_app, name="repo")
app.add_typer(pr_app, name="pr")
app.add_typer(branch_app, name="branch")
app.add_typer(commit_app, name="commit")
app.add_typer(pipeline_app, name="pipeline")


# ---------- helpers ----------

def _client() -> Client:
    return Client(load_config())


def _parse_repo(slug: str) -> tuple[str, str]:
    if "/" not in slug:
        raise ValidationError(f"expected WORKSPACE/REPO, got: {slug!r}")
    ws, repo = slug.split("/", 1)
    if not ws or not repo:
        raise ValidationError(f"expected WORKSPACE/REPO, got: {slug!r}")
    return ws, repo


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


def _json_or_empty(resp) -> dict:
    if resp.status_code == 204 or not resp.content:
        return {"ok": True, "status": resp.status_code}
    try:
        return resp.json()
    except ValueError:
        return {"ok": True, "status": resp.status_code, "text": resp.text}


# ---------- auth ----------

@auth_app.command("check")
def auth_check() -> None:
    """Verify credentials by calling /user."""
    with _client() as c:
        data = c.get_json("/user")
    emit_json(
        {
            "ok": True,
            "account_id": data.get("account_id"),
            "nickname": data.get("nickname"),
            "display_name": data.get("display_name"),
            "uuid": data.get("uuid"),
        }
    )


# ---------- raw / paginate (the escape hatches) ----------

@app.command("raw")
def raw(
    method: str = typer.Argument(..., help="HTTP method: GET/POST/PUT/PATCH/DELETE"),
    path: str = typer.Argument(..., help="API path, e.g. /repositories/{workspace}"),
    query: list[str] = typer.Option(
        [], "--query", "-q", help="KEY=VALUE query param (repeatable)"
    ),
    data: Optional[str] = typer.Option(
        None, "--data", "-d", help="JSON body string, or @path/to/file.json"
    ),
    print_url: bool = typer.Option(
        False, "--print-url", help="Print the URL that would be called and exit."
    ),
) -> None:
    """Make a raw authenticated request. Escape hatch for any endpoint."""
    params = _parse_query(query)
    body = _load_data(data)

    if print_url:
        rel = path if path.startswith("/") else "/" + path
        full = f"{BASE_URL}{rel}"
        if params:
            full += "?" + urlencode(params)
        emit_json({"method": method.upper(), "url": full, "body": body})
        return

    with _client() as c:
        resp = c.request(method.upper(), path, params=params, json=body)

    if resp.status_code == 204 or not resp.content:
        emit_json({"ok": True, "status": resp.status_code})
        return
    try:
        emit_json(resp.json())
    except ValueError:
        emit_raw(resp.text)


@app.command("paginate")
def paginate(
    path: str = typer.Argument(..., help="Paginated API path"),
    query: list[str] = typer.Option([], "--query", "-q"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Max items to return"),
) -> None:
    """Follow `next` links and emit a JSON array of all values."""
    params = _parse_query(query)
    with _client() as c:
        items = list(c.paginate(path, params=params, limit=limit))
    emit_json(items)


# ---------- repo ----------

@repo_app.command("list")
def repo_list(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Limit to a workspace slug"
    ),
    role: Optional[str] = typer.Option(
        None, "--role", help="owner/admin/contributor/member"
    ),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    """List repositories visible to the authenticated user."""
    path = f"/repositories/{workspace}" if workspace else "/repositories"
    params = {"role": role} if role else None
    with _client() as c:
        items = list(c.paginate(path, params=params, limit=limit))
    emit_json(items)


@repo_app.command("get")
def repo_get(slug: str = typer.Argument(..., help="WORKSPACE/REPO")) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        emit_json(c.get_json(f"/repositories/{ws}/{repo}"))


# ---------- pr ----------

@pr_app.command("list")
def pr_list(
    slug: str = typer.Argument(..., help="WORKSPACE/REPO"),
    state: Optional[str] = typer.Option(
        None, "--state", help="OPEN/MERGED/DECLINED/SUPERSEDED"
    ),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    ws, repo = _parse_repo(slug)
    params = {"state": state.upper()} if state else None
    with _client() as c:
        items = list(
            c.paginate(
                f"/repositories/{ws}/{repo}/pullrequests",
                params=params,
                limit=limit,
            )
        )
    emit_json(items)


@pr_app.command("get")
def pr_get(
    slug: str = typer.Argument(...),
    pr_id: int = typer.Argument(...),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        emit_json(c.get_json(f"/repositories/{ws}/{repo}/pullrequests/{pr_id}"))


@pr_app.command("diff")
def pr_diff(
    slug: str = typer.Argument(...),
    pr_id: int = typer.Argument(...),
) -> None:
    """Print the raw unified diff of a PR."""
    ws, repo = _parse_repo(slug)
    with _client() as c:
        resp = c.request(
            "GET",
            f"/repositories/{ws}/{repo}/pullrequests/{pr_id}/diff",
            accept="text/plain",
        )
    emit_raw(resp.text)


@pr_app.command("comments")
def pr_comments(
    slug: str = typer.Argument(...),
    pr_id: int = typer.Argument(...),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        items = list(
            c.paginate(
                f"/repositories/{ws}/{repo}/pullrequests/{pr_id}/comments",
                limit=limit,
            )
        )
    emit_json(items)


@pr_app.command("create")
def pr_create(
    slug: str = typer.Argument(...),
    source: str = typer.Option(..., "--source", help="Source branch name"),
    dest: str = typer.Option(..., "--dest", help="Destination branch name"),
    title: str = typer.Option(..., "--title"),
    body: Optional[str] = typer.Option(None, "--body", help="PR description (markdown)"),
    close_source: bool = typer.Option(
        False, "--close-source", help="Close source branch after merge"
    ),
) -> None:
    ws, repo = _parse_repo(slug)
    payload: dict = {
        "title": title,
        "source": {"branch": {"name": source}},
        "destination": {"branch": {"name": dest}},
        "close_source_branch": close_source,
    }
    if body:
        payload["description"] = body
    with _client() as c:
        resp = c.request(
            "POST", f"/repositories/{ws}/{repo}/pullrequests", json=payload
        )
    emit_json(_json_or_empty(resp))


@pr_app.command("approve")
def pr_approve(
    slug: str = typer.Argument(...),
    pr_id: int = typer.Argument(...),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        resp = c.request(
            "POST", f"/repositories/{ws}/{repo}/pullrequests/{pr_id}/approve"
        )
    emit_json(_json_or_empty(resp))


@pr_app.command("merge")
def pr_merge(
    slug: str = typer.Argument(...),
    pr_id: int = typer.Argument(...),
    strategy: str = typer.Option(
        "merge_commit",
        "--strategy",
        help="merge_commit/squash/fast_forward",
    ),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        resp = c.request(
            "POST",
            f"/repositories/{ws}/{repo}/pullrequests/{pr_id}/merge",
            json={"merge_strategy": strategy},
        )
    emit_json(_json_or_empty(resp))


# ---------- branch ----------

@branch_app.command("list")
def branch_list(
    slug: str = typer.Argument(...),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        items = list(
            c.paginate(f"/repositories/{ws}/{repo}/refs/branches", limit=limit)
        )
    emit_json(items)


# ---------- commit ----------

@commit_app.command("get")
def commit_get(
    slug: str = typer.Argument(...),
    sha: str = typer.Argument(...),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        emit_json(c.get_json(f"/repositories/{ws}/{repo}/commit/{sha}"))


# ---------- pipeline ----------

@pipeline_app.command("list")
def pipeline_list(
    slug: str = typer.Argument(...),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        items = list(
            c.paginate(f"/repositories/{ws}/{repo}/pipelines/", limit=limit)
        )
    emit_json(items)


@pipeline_app.command("get")
def pipeline_get(
    slug: str = typer.Argument(...),
    uuid: str = typer.Argument(..., help="Pipeline UUID (include braces if present)"),
) -> None:
    ws, repo = _parse_repo(slug)
    with _client() as c:
        emit_json(c.get_json(f"/repositories/{ws}/{repo}/pipelines/{uuid}"))


@pipeline_app.command("logs")
def pipeline_logs(
    slug: str = typer.Argument(...),
    uuid: str = typer.Argument(...),
    step_uuid: str = typer.Argument(...),
) -> None:
    """Print raw log text for a pipeline step."""
    ws, repo = _parse_repo(slug)
    with _client() as c:
        resp = c.request(
            "GET",
            f"/repositories/{ws}/{repo}/pipelines/{uuid}/steps/{step_uuid}/log",
            accept="text/plain",
        )
    emit_raw(resp.text)


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
    except BBError as e:
        emit_error(str(e))
        sys.exit(e.exit_code)
    except Exception as e:  # last-resort guard so we always emit to stderr
        emit_error(f"unexpected: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
