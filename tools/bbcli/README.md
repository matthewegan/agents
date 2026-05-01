# bbcli

An agent-friendly CLI for the Bitbucket Cloud REST API.

## Design

- **JSON to stdout, errors to stderr.** Clean separation for scripting and agents.
- **Stable exit codes.** `0` ok, `1` general, `2` auth, `3` not found, `4` validation, `5` config.
- **Raw escape hatch.** `bb raw METHOD PATH` hits any endpoint, wrapped or not.
- **Auto-pagination.** List commands follow `next` until exhausted. Use `--limit` to cap.
- **No interactive prompts.** Credentials come from env or config file, never stdin.

## Install

```sh
uv tool install --from /Users/matt.egan/dev/tools/bbcli bbcli
```

Re-install after edits:

```sh
uv tool install --force --from /Users/matt.egan/dev/tools/bbcli bbcli
```

## Auth

Uses HTTP Basic auth with your Atlassian email + a personal API token.
Create one at <https://id.atlassian.com/manage-profile/security/api-tokens>.

Give it at least the scopes you'll need — typically `read:account`,
`read:repository:bitbucket`, `write:repository:bitbucket`,
`read:pullrequest:bitbucket`, `write:pullrequest:bitbucket`.

### Environment variables (recommended)

```sh
export BITBUCKET_EMAIL="you@example.com"
export BITBUCKET_API_TOKEN="ATATT..."
```

### Config file (fallback)

`~/.config/bbcli/config.toml`:

```toml
email = "you@example.com"
api_token = "ATATT..."
```

Env vars override the config file.

### Verify

```sh
bb auth check
```

Prints your account info as JSON on success, exits `2` with an error on stderr
if the token is bad.

## Commands

`WORKSPACE/REPO` may be omitted from any command when run inside a Bitbucket
Cloud clone — `bb` parses `git remote get-url origin` to fill it in.

```
bb auth check

bb raw METHOD PATH [--query k=v]... [--data '{...}' | --data @body.json] [--print-url]
bb paginate PATH [--query k=v]... [--limit N]

bb repo list [--workspace WS] [--role ROLE] [--limit N]
bb repo get [WORKSPACE/REPO]

bb pr list [WORKSPACE/REPO] [--state OPEN|MERGED|DECLINED|SUPERSEDED] [--limit N]
bb pr get [WORKSPACE/REPO] PR_ID
bb pr diff [WORKSPACE/REPO] PR_ID
bb pr comments [WORKSPACE/REPO] PR_ID [--limit N]
bb pr create [WORKSPACE/REPO] --source BR --dest BR --title T [--body B] [--close-source]
bb pr approve [WORKSPACE/REPO] PR_ID
bb pr merge [WORKSPACE/REPO] PR_ID [--strategy merge_commit|squash|fast_forward]

bb branch list [WORKSPACE/REPO] [--limit N]

bb commit get [WORKSPACE/REPO] SHA

bb pipeline list [WORKSPACE/REPO] [--limit N]
bb pipeline get [WORKSPACE/REPO] UUID
bb pipeline logs [WORKSPACE/REPO] UUID STEP_UUID
```

Run `bb --help` or `bb <group> --help` for full details.

## Examples

```sh
# Who am I
bb auth check

# List repos in a workspace
bb repo list --workspace myworkspace

# Open PRs in a repo
bb pr list myworkspace/myrepo --state OPEN

# Fetch a PR and its diff
bb pr get myworkspace/myrepo 42
bb pr diff myworkspace/myrepo 42

# Create a PR
bb pr create myworkspace/myrepo \
  --source feature/x \
  --dest main \
  --title "Add x" \
  --body "Closes #123"

# Raw passthrough for anything not wrapped
bb raw GET /workspaces/myworkspace/members --query pagelen=50
bb raw POST /repositories/myworkspace/myrepo/issues \
  --data '{"title":"bug","content":{"raw":"reproduces on main"}}'

# Preview without calling
bb raw GET /user --print-url

# Walk every page of an endpoint
bb paginate /repositories/myworkspace --limit 500
```

## Agent usage notes

When directing an agent to use this CLI:

- Tell it to parse stdout as JSON and check exit codes.
- `bb raw` covers anything not wrapped — no need to add a new subcommand for
  every endpoint.
- For anything paginated, prefer `bb paginate PATH` over hand-looping `bb raw`.
- `bb raw ... --print-url` lets the agent dry-run before making changes.
