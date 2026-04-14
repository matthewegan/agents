---
name: bbcli
description: Bitbucket Cloud CLI (`bb`) reference for repositories, pull requests, branches, commits, and pipelines on Bitbucket Cloud. Use ONLY when the user explicitly mentions Bitbucket, refers to the `bb` command by name, pastes a bitbucket.org URL, or the current working directory's git remote points to bitbucket.org. Do NOT activate for generic "pull request", "repo", "CI", or "merge" requests that could apply to GitHub — the separate `gh-cli` skill handles GitHub. When a request is ambiguous, run `git remote -v` first to decide.
---

# bbcli — Bitbucket Cloud CLI

`bb` is a locally-installed, agent-friendly wrapper around the Bitbucket Cloud REST API v2.0. Source lives in this repo at `tools/bbcli/`, installed via `uv tool install`.

## When to use this skill

Use `bb` for Bitbucket Cloud operations when **any** of these is true:

- The user says "Bitbucket", "bb", "Atlassian repo", or similar.
- The user pastes a `bitbucket.org/...` URL.
- `git remote -v` in the current working directory shows `bitbucket.org`.
- The user has an open PR, repo, or pipeline context that is already established as Bitbucket in this conversation.

## When NOT to use this skill

- When the user says "GitHub", "gh", or pastes a `github.com` URL → use the `gh-cli` skill instead.
- When `git remote -v` shows `github.com` → use `gh-cli`.
- When the request is purely local git (commit, rebase, diff between local branches) → use plain `git`, not `bb`.

## Disambiguation protocol (important)

If the user's request mentions "PR", "pull request", "repo", "CI", "pipeline", "merge", or similar words **without naming the platform**, do NOT guess. Follow this sequence:

1. **Check the current repo.** Run `git remote -v`. If it contains `bitbucket.org`, use `bb`. If it contains `github.com`, use `gh`. Done.
2. **Check prior conversation context.** If Bitbucket or GitHub was already established in this session, stick with that platform.
3. **Ask.** If steps 1 and 2 don't resolve it, ask one short question: "Is this a Bitbucket or GitHub repo?"

Never run destructive or stateful commands (create/merge/approve PR, trigger pipeline) against the wrong platform because of a guess.

## Prerequisites

### Installation

Already installed. Verify with:

```sh
which bb && bb --help
```

If missing, reinstall from source (path relative to repo root):

```sh
uv tool install --force /path/to/agents/tools/bbcli
```

### Authentication

`bb` uses HTTP Basic auth: Atlassian email + personal API token. Tokens are created at <https://id.atlassian.com/manage-profile/security/api-tokens>.

Credentials come from (in priority order):

1. `BITBUCKET_EMAIL` and `BITBUCKET_API_TOKEN` environment variables.
2. `~/.config/bbcli/config.toml` with keys `email` and `api_token`.

`bb` never prompts interactively — if credentials are missing, it exits 5 with an error on stderr.

Verify auth:

```sh
bb auth check
```

Returns JSON with account info on success.

## Design contract

`bb` is designed for scripting and agent use. Rely on these guarantees:

- **stdout is JSON** (or raw text for endpoints that return diffs/logs). Never mixed.
- **stderr is errors only.** Safe to redirect with `2>/dev/null`.
- **Exit codes are stable:**
  - `0` — success
  - `1` — general/unknown error
  - `2` — auth failure (401/403)
  - `3` — not found (404)
  - `4` — client-side validation or bad request
  - `5` — missing/invalid config
- **Pagination is automatic.** List commands follow `next` until exhausted. Use `--limit N` to cap.
- **No interactive prompts.** Suitable for non-TTY contexts.

## Command reference

### Auth

```sh
bb auth check                     # verify credentials, print account JSON
```

### Escape hatches (use for any unwrapped endpoint)

```sh
bb raw METHOD PATH [--query k=v]... [--data '{...}' | --data @body.json] [--print-url]
bb paginate PATH [--query k=v]... [--limit N]
```

`--print-url` is a dry run: prints the computed URL and body as JSON without making the request. Use it before any state-changing call to confirm the target.

### Repositories

```sh
bb repo list [--workspace WS] [--role owner|admin|contributor|member] [--limit N]
bb repo get WORKSPACE/REPO
```

### Pull requests

```sh
bb pr list WORKSPACE/REPO [--state OPEN|MERGED|DECLINED|SUPERSEDED] [--limit N]
bb pr get WORKSPACE/REPO PR_ID
bb pr diff WORKSPACE/REPO PR_ID                                    # raw diff text
bb pr comments WORKSPACE/REPO PR_ID [--limit N]
bb pr create WORKSPACE/REPO --source BR --dest BR --title T [--body B] [--close-source]
bb pr approve WORKSPACE/REPO PR_ID
bb pr merge WORKSPACE/REPO PR_ID [--strategy merge_commit|squash|fast_forward]
```

### Branches and commits

```sh
bb branch list WORKSPACE/REPO [--limit N]
bb commit get WORKSPACE/REPO SHA
```

### Pipelines

```sh
bb pipeline list WORKSPACE/REPO [--limit N]
bb pipeline get WORKSPACE/REPO UUID                                # UUID may include braces
bb pipeline logs WORKSPACE/REPO UUID STEP_UUID                     # raw log text
```

## Common recipes

### Find the workspace/repo from the current directory

```sh
git remote get-url origin
# → https://bitbucket.org/myws/myrepo.git   (or git@bitbucket.org:myws/myrepo.git)
```

Parse out `myws/myrepo` and pass it to `bb`.

### Summarise open PRs in this repo

```sh
bb pr list myws/myrepo --state OPEN \
  | jq '[.[] | {id, title, author: .author.display_name, src: .source.branch.name, dest: .destination.branch.name}]'
```

### Read a PR and its diff

```sh
bb pr get myws/myrepo 42              # metadata as JSON
bb pr diff myws/myrepo 42             # unified diff as text
bb pr comments myws/myrepo 42         # review comments as JSON
```

### Create a PR

```sh
bb pr create myws/myrepo \
  --source feature/x \
  --dest main \
  --title "Add x" \
  --body "Closes https://myws.atlassian.net/browse/ENG-123"
```

### Inspect a failing pipeline

```sh
bb pipeline list myws/myrepo --limit 5
bb pipeline get myws/myrepo '{uuid-from-list}'
bb pipeline logs myws/myrepo '{pipeline-uuid}' '{step-uuid}'
```

### Hit an unwrapped endpoint

```sh
# Workspace members (no dedicated subcommand)
bb raw GET /workspaces/myws/members --query pagelen=50

# Create an issue via POST
bb raw POST /repositories/myws/myrepo/issues \
  --data '{"title":"bug","content":{"raw":"reproduces on main"}}'

# Dry run first — print the URL and body, don't send
bb raw POST /repositories/myws/myrepo/issues --data @body.json --print-url
```

### Walk every page of a list endpoint

```sh
bb paginate /repositories/myws --limit 1000
```

## Error handling guidance

When scripting `bb`, check exit codes — don't parse error text:

```sh
if ! bb pr get myws/myrepo 42 > pr.json 2> err.txt; then
  case $? in
    2) echo "auth problem — token expired?" ;;
    3) echo "PR doesn't exist" ;;
    4) echo "bad request: $(cat err.txt)" ;;
    5) echo "credentials not configured" ;;
    *) echo "unknown failure: $(cat err.txt)" ;;
  esac
  exit 1
fi
```

## Safety rules for state-changing commands

Before running any of these without explicit user confirmation, stop and confirm with the user first:

- `bb pr create`
- `bb pr approve`
- `bb pr merge`
- `bb raw POST|PUT|PATCH|DELETE ...`

For `bb raw` with a mutating method, preview with `--print-url` first and show the user what will be called before executing for real. Approval for one mutating call is NOT blanket approval for others — confirm each distinct action.

## Source and extending

- Source: `tools/bbcli/` (relative to this repo's root)
- Entry point: `bbcli/cli.py`
- HTTP client: `bbcli/client.py`
- Reinstall after edits: `uv tool install --force /path/to/agents/tools/bbcli`

To add a new convenience command, prefer `bb raw` first — if the pattern repeats, add a wrapper in `cli.py` following the existing sub-app structure.

## Reference docs

The official Bitbucket Cloud REST API docs are at <https://developer.atlassian.com/cloud/bitbucket/rest/>. Consult them when building new wrappers or when you need to understand a specific endpoint's request/response shape.
