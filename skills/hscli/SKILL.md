---
name: hscli
description: HubSpot API CLI (`hscli`) reference for CMS landing pages, module discovery, and general HubSpot API access. Use when the user mentions HubSpot CMS, landing pages, HubSpot modules, finding which pages use a module, HubSpot API queries, or refers to the `hscli` command by name. Also use when working in a directory with HubSpot CMS modules (e.g., `.module/` folders, `meta.json`/`fields.json` files, or HubL templates) and the user needs to query the live HubSpot account. Do NOT activate for HubSpot CLI project commands (`hs project`, `hs cms upload`) — those use the official `hs` CLI, not `hscli`.
---

# hscli — HubSpot API CLI

`hscli` is a locally-installed, agent-friendly wrapper around the HubSpot REST API. Source lives in this repo at `tools/hscli/`, installed via `uv tool install`.

## When to use this skill

Use `hscli` for querying the HubSpot API when **any** of these is true:

- The user mentions HubSpot CMS, landing pages, or HubSpot modules.
- The user wants to find which landing pages use a particular module.
- The user wants to list, filter, or inspect landing pages on HubSpot.
- The user needs to make authenticated requests to any HubSpot API endpoint.
- The user refers to `hscli` by name.
- You're working in a HubSpot CMS modules directory and need to check live page data.

## When NOT to use this skill

- For HubSpot CLI project operations (`hs project create`, `hs cms upload`, `hs project dev`) — those use the official `hs` CLI.
- For editing local HubSpot module files (`.module/` directories with `meta.json`, `fields.json`, `module.html`) — just edit the files directly.
- For HubSpot MCP server tools (`mcp__HubSpotDev__*`) — those are a separate integration.

## Prerequisites

### Installation

Already installed. Verify with:

```sh
which hscli && hscli --help
```

If missing, reinstall from source (path relative to repo root):

```sh
uv tool install --force /path/to/agents/tools/hscli
```

### Authentication

`hscli` automatically reads credentials from the HubSpot CLI config — no separate setup required.

Credentials come from (in priority order):

1. `HUBSPOT_ACCESS_TOKEN` environment variable (override).
2. `~/.hscli/config.yml` (HubSpot CLI config) — reads the `personalAccessKey` and automatically exchanges it for a short-lived API token. Cached tokens are reused until expiry.

If the HubSpot CLI isn't authenticated yet, the user needs to run:

```sh
npm install -g @hubspot/cli@latest
hs account auth
```

`hscli` never prompts interactively — if credentials are missing, it exits 5 with an error on stderr.

Verify auth:

```sh
hscli auth check
```

Returns JSON with API usage info on success.

## Design contract

`hscli` is designed for scripting and agent use. Rely on these guarantees:

- **stdout is JSON.** Never mixed with errors.
- **stderr is errors only.** Safe to redirect with `2>/dev/null`.
- **Exit codes are stable:**
  - `0` — success
  - `1` — general/unknown error
  - `2` — CLI usage error (bad flags/args)
  - `3` — not found (404)
  - `4` — client-side validation or bad request
  - `5` — missing/invalid config
  - `10` — auth failure (401/403)
- **Pagination is automatic.** List commands follow HubSpot's `after` cursors until exhausted. Use `--limit N` to cap.
- **No interactive prompts.** Suitable for non-TTY contexts.

## Command reference

### Auth

```sh
hscli auth check                    # verify credentials, print API usage JSON
```

### Escape hatches (use for any unwrapped endpoint)

```sh
hscli raw METHOD PATH [--query k=v]... [--data '{...}' | --data @body.json]
hscli paginate PATH [--query k=v]... [--limit N]
```

### CMS — Landing Pages

```sh
hscli cms landing-pages list [--state PUBLISHED|DRAFT] [--name SUBSTRING] [--limit N] [--query k=v]...
hscli cms landing-pages get PAGE_ID
hscli cms landing-pages find-by-module MODULE [--state PUBLISHED|DRAFT] [--scan-limit N] [--limit N]
```

#### Key command: `find-by-module`

This is the primary use case — finding which landing pages use a specific module. It fetches pages from the API and inspects their `layoutSections` recursively for module paths matching the given string (case-insensitive substring match).

- `MODULE` — the module path or substring to search for (e.g., `"rich_text"`, `"calendly-popup-button"`, `"custom-cta"`)
- `--scan-limit N` — limits how many pages are fetched from the API (controls API calls)
- `--limit N` — limits how many matching results are returned (controls output size)
- `--state` — filter to only PUBLISHED or DRAFT pages before scanning

Output is a JSON array of matches, each containing `id`, `name`, `slug`, `state`, `url`, `updatedAt`, and `matched_modules` (the specific module paths that matched).

## Common recipes

### Find all published landing pages using a specific module

```sh
hscli cms landing-pages find-by-module "calendly-popup-button" --state PUBLISHED
```

### List all landing pages, filtered by name

```sh
hscli cms landing-pages list --name "campaign" --state PUBLISHED
```

### Get full details of a specific landing page

```sh
hscli cms landing-pages get 177898049056
```

### Summarise landing pages using a module

```sh
hscli cms landing-pages find-by-module "rich_text" --limit 10 \
  | jq '[.[] | {name, url, modules: .matched_modules}]'
```

### Hit an unwrapped endpoint

```sh
# Site pages (not landing pages)
hscli raw GET /cms/v3/pages/site-pages

# With query params
hscli raw GET /cms/v3/pages/landing-pages -q state=PUBLISHED -q limit=5

# POST with JSON body
hscli raw POST /some/endpoint -d '{"key": "value"}'

# POST with body from file
hscli raw POST /some/endpoint -d @payload.json
```

### Walk every page of a list endpoint

```sh
hscli paginate /cms/v3/pages/landing-pages -q state=PUBLISHED --limit 100
```

## Error handling guidance

When scripting `hscli`, check exit codes — don't parse error text:

```sh
if ! hscli cms landing-pages get 12345 > page.json 2> err.txt; then
  case $? in
    10) echo "auth problem — run 'hs account auth' to refresh" ;;
    3)  echo "page doesn't exist" ;;
    4)  echo "bad request: $(cat err.txt)" ;;
    5)  echo "credentials not configured — run 'hs account auth'" ;;
    *)  echo "unknown failure: $(cat err.txt)" ;;
  esac
  exit 1
fi
```

## HubSpot API filtering

When using `--query` or the `raw`/`paginate` escape hatches, HubSpot supports these filter operators on properties:

```
propertyName__operator=value
```

Operators: `eq`, `ne`, `contains`, `icontains`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`, `startswith`, `not_null`

Useful filterable properties for landing pages: `id`, `slug`, `name`, `state`, `publishDate`, `createdAt`, `updatedAt`, `templatePath`, `domain`.

## Source and extending

- Source: `tools/hscli/` (relative to this repo's root)
- Entry point: `hscli/cli.py`
- HTTP client: `hscli/client.py`
- Config/auth: `hscli/config.py`
- Reinstall after edits: `uv tool install --force /path/to/agents/tools/hscli`

To add a new convenience command, prefer `hscli raw` first — if the pattern repeats, add a wrapper in `cli.py` following the existing sub-app structure (create a new Typer sub-app under `cms_app` or directly under `app`).
