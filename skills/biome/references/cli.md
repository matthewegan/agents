# Biome CLI reference

Every subcommand, every flag, exit codes, environment variables. For config-file options see `configuration.md`.

## Subcommands

| Command | Purpose |
|---|---|
| `biome check` | Format + lint + assist. Read-only by default; `--write` applies safe fixes. |
| `biome ci` | Read-only CI runner. Refuses `--write`. Auto GitHub annotations. Supports `--changed`, not `--staged`. |
| `biome format` | Formatter only. `--write` applies. |
| `biome lint` | Linter only. `--write` applies safe fixes; `--unsafe` also applies unsafe ones. |
| `biome assist` | Assist actions only (import sort, key sort, etc.). |
| `biome init` | Scaffold `biome.json` (add `--jsonc` for `biome.jsonc`). |
| `biome migrate prettier` | Port `.prettierrc*` into the current `biome.json`. Use `--write` to apply. |
| `biome migrate eslint` | Port `.eslintrc*` (legacy or flat) into the current `biome.json`. `--include-inspired` pulls in Biome rules that are "inspired by" ESLint ones, not just strict equivalents. |
| `biome migrate` | (After upgrading from v1) rewrite `biome.json` / `biome.jsonc` to v2 shape. `--write` to apply. |
| `biome explain <category>` | Print docs for a rule (e.g., `biome explain lint/suspicious/noExplicitAny`). |
| `biome search '<GritQL>'` | EXPERIMENTAL. Find code matching a GritQL pattern across the project. |
| `biome rage` | Dump diagnostic info for bug reports. |
| `biome version` | Print version and exit. |
| `biome clean` | Clean daemon logs. |
| `biome start` / `biome stop` | Start/stop the daemon explicitly. Normally managed automatically. |
| `biome lsp-proxy` | LSP server over stdin/stdout (for editors). |

## Flags

### Writing / fixing

| Flag | Effect |
|---|---|
| `--write`, `--fix` | Apply safe formatting and safe lint fixes (aliases). |
| `--unsafe` | Additionally apply fixes flagged unsafe (behavior-changing). Must be combined with `--write`/`--fix`. |

### File selection

| Flag | Effect |
|---|---|
| `--staged` | Only git-staged files. Requires `vcs.enabled: true`. **Not** available in `biome ci`. |
| `--changed` | Only files changed vs. `vcs.defaultBranch`. Requires `vcs.enabled: true`. |
| `--since=<REF>` | Override `vcs.defaultBranch` for `--changed`. |
| `--stdin-file-path=<path>` | Read source from stdin; `<path>` determines language/overrides. |
| `--files-ignore-unknown=true` | Silently skip unknown file types (safer in hooks). |
| `--no-errors-on-unmatched` | Exit 0 instead of erroring when the passed paths match nothing (critical for `--staged` hooks). |

### Rule / tool filtering

| Flag | Effect |
|---|---|
| `--only=<rule\|group\|domain\|action>` | Run only the matched items. Repeatable. |
| `--skip=<rule\|group\|domain\|action>` | Skip the matched items. Repeatable. `--skip` wins over `--only`. |
| `--formatter-enabled=<true\|false>` | Enable/disable the formatter for this run. |
| `--linter-enabled=<true\|false>` | Enable/disable the linter for this run. |
| `--assist-enabled=<true\|false>` | Enable/disable assist for this run. |
| `--enforce-assist=<true\|false>` | If false, assist actions are advisory, not required. |

### Reporters

`--reporter=<default|json|json-pretty|github|junit|summary|gitlab|checkstyle|rdjson|sarif>`

| Value | Notes |
|---|---|
| `default` | Human-readable diagnostics (default). |
| `summary` | One-line-per-file aggregate. Useful for CI logs. |
| `github` | GitHub Actions annotations. Auto-selected under `GITHUB_ACTIONS=true` for `biome ci`. |
| `junit` | JUnit XML — for CI dashboards. Pair with `--reporter-file`. |
| `gitlab` | GitLab Code Quality JSON. |
| `json`, `json-pretty` | Machine-readable diagnostics. |
| `checkstyle` | Checkstyle XML. |
| `rdjson` | reviewdog JSON. |
| `sarif` | SARIF JSON. |

Related: `--reporter-file=<path>`, `--max-diagnostics=<N>|none` (default 20), `--diagnostic-level=<info|warn|error>`, `--error-on-warnings`.

### Per-language overrides (inline)

Every language has CLI equivalents of its formatter/parser config. Useful for one-off ad-hoc runs:

```
--javascript-formatter-indent-style=<tab|space>
--javascript-formatter-indent-width=<N>
--javascript-formatter-line-ending=<lf|crlf|cr|auto>
--javascript-formatter-line-width=<N>
--javascript-formatter-quote-style=<double|single>
--javascript-formatter-jsx-quote-style=<double|single>
--javascript-formatter-trailing-commas=<all|es5|none>
--javascript-formatter-semicolons=<always|as-needed>
--javascript-formatter-arrow-parentheses=<always|as-needed>
--javascript-formatter-bracket-spacing=<true|false>
--javascript-formatter-bracket-same-line=<true|false>

--json-formatter-trailing-commas=<none|all>
--json-parse-allow-comments=<true|false>
--json-parse-allow-trailing-commas=<true|false>

--css-formatter-quote-style=<double|single>
--css-parse-css-modules=<true|false>
--css-parse-tailwind-directives=<true|false>

--graphql-formatter-quote-style=<double|single>

--html-formatter-whitespace-sensitivity=<css|strict|ignore>
--html-formatter-self-close-void-elements=<always|never>
```

### VCS

```
--vcs-enabled=<true|false>
--vcs-client-kind=<git>
--vcs-use-ignore-file=<true|false>
--vcs-root=<path>
--vcs-default-branch=<branch>
```

### Daemon / logging

```
--use-server               # route this CLI call through the running daemon (faster for repeated runs)
--log-level=<none|debug|info|warn|error>
--log-kind=<pretty|compact|json>
--log-file=<path>
--log-path=<path>          # daemon only
--colors=<off|force>
```

### Config resolution

```
--config-path=<PATH>       # explicit config file or containing dir (disables default resolution)
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Clean |
| 1 | Diagnostics emitted, or unsafe fixes needed |
| 2 | CLI / configuration error |
| 101 | Fatal error (filesystem, parse error, panic) |

## Environment variables

| Var | Equivalent flag |
|---|---|
| `BIOME_CONFIG_PATH` | `--config-path` |
| `BIOME_LOG_LEVEL` | `--log-level` |
| `BIOME_LOG_FILE` | `--log-file` (CLI only) |
| `BIOME_LOG_KIND` | `--log-kind` |
| `BIOME_LOG_PATH` | `--log-path` (daemon only) |
| `BIOME_LOG_PREFIX_NAME` | log filename prefix |
| `BIOME_THREADS` | worker thread count for `biome ci` |

## Workflow recipes

```shell
# Pre-commit (lefthook / husky): safe fixes on staged files, never error on empty list
biome check --write --staged --no-errors-on-unmatched --files-ignore-unknown=true

# CI (GitHub): annotations, read-only
biome ci .

# CI (GitLab): Code Quality report
biome ci --reporter=gitlab --colors=off > code-quality.json

# Changed files vs. custom branch
biome ci --changed --since=develop

# Format stdin → stdout (editors/tools)
echo 'const x  =  1' | biome check --stdin-file-path=test.ts --write

# Fast feedback: skip style warnings
biome check --skip=style

# Just React rules
biome check --only=react

# Machine-readable diagnostics
biome ci --reporter=json-pretty --reporter-file=report.json

# Find slow files
biome lint --log-level=tracing --log-kind=json --log-file=tracing.json
# Then: jq 'select(.span.name == "pull_diagnostics") | {path: .span.path, time: .["time.busy"]}' tracing.json
```

## Things NOT to do

- **Don't shell-glob Biome.** `biome lint 'src/**/*.ts'` expands in your shell, not Biome; use `files.includes` instead.
- **Don't mix `--write` with `biome ci`.** CI rejects the flag.
- **Don't use `--staged` in CI.** Use `--changed --since=<base>` instead.
- **Don't forget `--no-errors-on-unmatched` in hooks.** Otherwise an empty staged-files list fails the commit.
