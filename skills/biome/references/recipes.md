# Biome recipes

Workflow patterns: git hooks, CI, editor wiring, monorepo, troubleshooting slowness, Renovate.

## Pre-commit hooks

### lefthook (recommended — zero-dep, cross-platform)

```yaml
# lefthook.yml (at repo root)
pre-commit:
  commands:
    biome:
      glob: "*.{js,ts,cjs,mjs,d.cts,d.mts,jsx,tsx,json,jsonc,css,graphql,gql}"
      run: npx @biomejs/biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true       # re-add files after auto-fix
```

Install: `npx lefthook install`.

### lint-staged + husky

```json
// package.json
{
  "scripts": {
    "prepare": "husky"
  },
  "lint-staged": {
    "*.{js,ts,cjs,mjs,jsx,tsx,json,jsonc,css,graphql,gql}": [
      "biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"
    ]
  }
}
```

```sh
# .husky/pre-commit
#!/usr/bin/env sh
npx lint-staged
```

### pre-commit framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/biomejs/pre-commit
    rev: v2.0.6
    hooks:
      - id: biome-check
        additional_dependencies: ["@biomejs/biome@2.4.13"]
```

### Plain shell hook (no framework)

```sh
# .git/hooks/pre-commit (chmod +x)
#!/bin/sh
set -eu
npx @biomejs/biome check --staged --no-errors-on-unmatched --files-ignore-unknown=true
```

### Things to always include

- `--no-errors-on-unmatched` — empty staged list shouldn't fail the commit.
- `--files-ignore-unknown=true` — don't error on e.g. `.md` files in staged changes.
- `--write` — actually fix things (pair with `stage_fixed: true` in lefthook).

### Things to avoid in hooks

- Running `biome ci` in a pre-commit hook. `ci` is read-only and slower; use `check` with `--staged` or `--write`.
- Running full-tree `biome check` in pre-commit. It's too slow on large repos; use `--staged` or `--changed` to scope.

## CI

### GitHub Actions

```yaml
# .github/workflows/biome.yml
name: Code quality
on:
  pull_request:
  push:
    branches: [main]

jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          persist-credentials: false
          fetch-depth: 0        # needed for --changed against base branch
      - uses: biomejs/setup-biome@v2
        with:
          version: latest       # or pin to 2.4.13
      - run: biome ci .
```

`biome ci` auto-emits GitHub annotations under `GITHUB_ACTIONS=true`. No reporter flag needed.

If your Biome config `extends` an npm package, install deps first:

```yaml
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: "pnpm" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec biome ci .
```

### Changed files only (faster)

```yaml
- run: biome ci --changed --since=origin/${{ github.base_ref || 'main' }}
```

### GitLab CI

```yaml
biome:
  image: node:22
  script:
    - npm ci
    - npx @biomejs/biome ci --reporter=gitlab --colors=off > gl-code-quality-report.json
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

### Bitbucket Pipelines

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Biome
          image: node:22
          caches: [node, pnpm]
          script:
            - pnpm install --frozen-lockfile
            - pnpm exec biome ci . --reporter=junit --reporter-file=biome.junit.xml
          artifacts:
            - biome.junit.xml
```

### Circle / Jenkins / elsewhere

Pick `--reporter=checkstyle` or `--reporter=junit` and save as an artifact; most CI systems can ingest one of those. `--reporter=sarif` is widely supported by code-scanning dashboards.

## Editor setup

### VS Code

```jsonc
// .vscode/settings.json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit",
    "quickfix.biome": "explicit"
  },
  "[typescript]":      { "editor.defaultFormatter": "biomejs.biome" },
  "[typescriptreact]": { "editor.defaultFormatter": "biomejs.biome" },
  "[javascript]":      { "editor.defaultFormatter": "biomejs.biome" },
  "[javascriptreact]": { "editor.defaultFormatter": "biomejs.biome" },
  "[json]":            { "editor.defaultFormatter": "biomejs.biome" },
  "[jsonc]":           { "editor.defaultFormatter": "biomejs.biome" },
  "[css]":             { "editor.defaultFormatter": "biomejs.biome" },
  "[vue]":             { "editor.defaultFormatter": "biomejs.biome" },
  // Use Biome even without a biome.json
  "biomejs.requireConfiguration": false
}
```

Recommend contributors install `biomejs.biome` via `.vscode/extensions.json`:

```json
{ "recommendations": ["biomejs.biome"] }
```

Also: **disable the Prettier and ESLint extensions for Biome-handled paths** so they don't fight over format-on-save.

### Zed

Biome is bundled. In `.zed/settings.json`:

```json
{
  "formatter": "biome",
  "[biome]": { "enabled": true }
}
```

### JetBrains

Install the official "Biome" plugin. Configure the path to your Biome binary (defaults to the project's `node_modules/.bin/biome`). Enable format-on-save in Settings → Tools → Actions on Save.

## Monorepo

Root `biome.jsonc`:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "files": {
    "ignoreUnknown": true,
    "includes": ["**", "!!**/node_modules", "!!**/dist", "!!**/.turbo", "!pnpm-lock.yaml"]
  },
  "formatter": { "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "javascript": { "formatter": { "quoteStyle": "single", "semicolons": "asNeeded", "trailingCommas": "all" } },
  "assist": { "enabled": true, "actions": { "source": { "organizeImports": "on" } } }
}
```

Package-level `packages/foo/biome.jsonc`:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "extends": "//",
  "root": false,
  "formatter": { "lineWidth": 120 },
  "linter": { "rules": { "suspicious": { "noConsole": "off" } } }
}
```

CI runs a single `biome ci .` from the repo root — Biome walks into each package and respects its nested config.

## Shared config via npm package

```json
// packages/biome-config/package.json
{
  "name": "@acme/biome-config",
  "version": "1.0.0",
  "exports": { "./biome": "./biome.json" }
}
```

```jsonc
// consumer biome.jsonc
{
  "extends": ["@acme/biome-config/biome"],
  "formatter": { "lineWidth": 120 }
}
```

Consumers need the config package installed: `pnpm add -D @acme/biome-config`.

## Renovate

Auto-update Biome and keep the `$schema` URL in sync:

```json
// renovate.json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchPackageNames": ["@biomejs/biome"],
      "description": "Update the schema URL in biome.json(c) alongside the version bump",
      "postUpgradeTasks": {
        "commands": [
          "npx -y replace-in-file 'schemas/[0-9.]+/schema.json' 'schemas/{{newVersion}}/schema.json' 'biome.json' 'biome.jsonc' --isRegex --glob"
        ]
      }
    }
  ]
}
```

## Troubleshooting slowness

Biome is usually fast; when it isn't, it's almost always the scanner.

### Quick wins

1. Exclude generated/build output with `!!` (not `!`):
   ```jsonc
   "files": { "includes": ["**", "!!**/dist", "!!**/.next", "!!**/.nuxt", "!!**/coverage"] }
   ```
   `!!` removes the files from scanner indexing entirely; `!` only excludes them from lint/format but still indexes them.
2. Disable `project` and `types` domains unless you specifically need them:
   ```jsonc
   "linter": { "domains": { "project": "off", "types": "off" } }
   ```
3. Raise `files.maxSize` only if needed; otherwise let large generated files be skipped.

### Tracing

```shell
biome lint --log-level=tracing --log-kind=json --log-file=trace.json
```

Slow-file inspection:

```shell
jq -c 'select(.span.name == "pull_diagnostics") | {path: .span.path, time_ms: (.["time.busy"]/1000000)}' trace.json \
  | sort -t: -k2 -n -r | head -20
```

Slow module-graph operations (when `project` domain is enabled):

```shell
jq -c 'select(.span.name == "update_module_graph_internal") | {path: .span.path, time_ms: (.["time.busy"]/1000000)}' trace.json \
  | sort -t: -k2 -n -r | head -20
```

### Daemon

Editors and `biome lsp-proxy` use a persistent daemon automatically. For repeated CLI runs in a tight inner loop, pass `--use-server`:

```shell
biome check --use-server
```

## Adopting Biome on a legacy codebase

First run will scream. Two strategies:

### Strategy A — accept the pain, fix in waves

```shell
pnpm exec biome check --write --unsafe
git add -u && git commit -m "chore: adopt biome (formatter pass)"
pnpm exec biome check    # see what's left
# Then demote noisy rules to warn, fix errors rule-group by rule-group
```

### Strategy B — start narrow, widen

Start with formatter only:
```jsonc
{ "linter": { "enabled": false }, "assist": { "enabled": false } }
```

Commit the re-format, then enable the linter with a minimal ruleset and expand:
```jsonc
{
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": false,
      "correctness": "error",
      "suspicious": "warn"
    }
  }
}
```

Add groups back as the team has time to address their backlog.

### Scoping by path

If a single subtree is in worse shape than the rest, scope Biome down first and expand later:

```jsonc
{ "files": { "includes": ["src/**", "scripts/**", "!src/legacy/**"] } }
```

## Useful one-liners

```shell
# What would biome do to this file?
biome check --write --verbose path/to/file.ts

# Explain a rule
biome explain lint/suspicious/noExplicitAny

# See all enabled rules given current config
biome lint --only=correctness --only=style --verbose  # noisy but shows what's active

# Filter output to just errors (drop warnings)
biome check --diagnostic-level=error

# Dry run of migration
biome migrate prettier    # omit --write to preview changes

# Find every file with at least one violation (JSON reporter + jq)
biome ci --reporter=json --max-diagnostics=none \
  | jq -r '.diagnostics[].location.path.file' | sort -u
```
