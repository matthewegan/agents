---
name: biome
description: "Biome v2 reference for formatting, linting, and import-sorting JavaScript, TypeScript, JSX/TSX, JSON/JSONC, CSS, GraphQL, and (experimentally) Vue/Svelte/Astro. Use this skill whenever the user is setting up, configuring, or troubleshooting Biome — whether they're adding `@biomejs/biome` to a project, writing or editing `biome.json`/`biome.jsonc`, migrating from ESLint and/or Prettier, running `biome format/lint/check/ci`, suppressing rules with `biome-ignore`, wiring up git hooks, or asking about Biome lint rules, formatter options, or CLI flags. Also use this skill any time Biome replaces Prettier or ESLint, or when you see a `biome.json`/`biome.jsonc` file in the project, even if the user doesn't explicitly mention Biome."
---

# Biome

Biome is a single toolchain for JavaScript / TypeScript / JSX / TSX / JSON / CSS / GraphQL projects. It replaces Prettier (formatting) and ESLint (linting) and also provides "assist" actions like import organizing. One binary, one config file, written in Rust, roughly an order of magnitude faster than the tools it replaces.

Current major version is **Biome v2**. This skill targets v2.x. If you see `rome.json`, `// rome-ignore`, or `organizeImports` at the top level of a config, that's v1 — see the v2 migration notes in `references/migration.md`.

## When to use this skill

- Adding Biome to a project (fresh install or replacing Prettier/ESLint)
- Authoring or editing `biome.json` / `biome.jsonc`
- Running or reading output from `biome format`, `biome lint`, `biome check`, `biome ci`
- Migrating Prettier/ESLint config (`biome migrate prettier/eslint`)
- Suppressing a rule at a file or line with `// biome-ignore …`
- Wiring Biome into pre-commit hooks, CI, or an editor
- Diagnosing Biome output — `lint/<group>/<ruleName>` diagnostic codes
- Upgrading Biome v1 → v2

## Mental model: three tools, one config

Biome exposes three pillars, all enabled by default, all configured in a single file:

| Pillar | Replaces | What it does |
|---|---|---|
| `formatter` | Prettier | Reformats whitespace, quotes, trailing commas, etc. |
| `linter` | ESLint + most plugins | Finds bugs, enforces style, auto-fixes where safe |
| `assist` | `eslint-plugin-import`, `organize-imports` | Source actions: sort imports, sort JSON keys, sort CSS props |

`biome check` runs all three. `biome format`, `biome lint`, and `biome assist` run one at a time. Most teams wire up `check` (dev) + `ci` (CI) and leave the single-tool commands for targeted runs.

Biome-isms to internalize:
- Biome refers to JS/TS/JSX/TSX collectively as **`javascript`** in the config. There's no separate `typescript` section; TypeScript-only options live under `javascript`.
- Glob patterns in `biome.json` are interpreted by **Biome**. On the CLI, your shell expands globs first — so prefer configuring `files.includes` over passing shell globs. In v2, `*` does **not** match `/`; use `**` for recursion. Paths are resolved relative to the config file's directory.
- Biome ignores files it doesn't recognize if `files.ignoreUnknown: true`; otherwise it emits a diagnostic per unknown file.
- `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `npm-shrinkwrap.json`, `composer.lock` are **always protected** — Biome never emits diagnostics for them.
- Some well-known JSON-ish files (`tsconfig.json`, `.eslintrc.json`, `.babelrc`, etc.) are auto-detected and parsed with comments/trailing-commas allowed where appropriate. You don't need overrides for those.

## Installation

Install pinned (`-E`) as a dev dependency. Version pinning matters — Biome ships formatting/rule changes in patch releases.

```shell
# npm
npm i -D -E @biomejs/biome
# pnpm
pnpm add -D -E @biomejs/biome
# yarn
yarn add -D -E @biomejs/biome
# bun
bun add -D -E @biomejs/biome
# deno
deno add -D npm:@biomejs/biome
```

Then generate a starter config:

```shell
npx @biomejs/biome init           # biome.json
npx @biomejs/biome init --jsonc   # biome.jsonc (prefer: comments + trailing commas)
```

**Prefer `biome.jsonc`** — the config is read frequently and you'll want to leave comments explaining non-default choices.

### Recommended `package.json` scripts

```json
{
  "scripts": {
    "format": "biome format --write",
    "lint": "biome lint",
    "lint:fix": "biome lint --write",
    "check": "biome check",
    "check:fix": "biome check --write",
    "ci": "biome ci"
  }
}
```

Why `check` vs `ci`: `check` is the dev command (supports `--write` and `--staged`). `ci` is strictly read-only, emits GitHub annotations when `GITHUB_ACTIONS=true`, supports `--changed` instead of `--staged`, and has CI-specific features like `BIOME_THREADS`. **Never run `biome check --write` in CI**, and **never pass `--write` to `biome ci`** — it'll reject the flag.

## Configuration

A canonical `biome.jsonc` for a modern Node/TS project, with each choice explained:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",

  // Respect .gitignore and enable --staged / --changed.
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  },

  "files": {
    // Skip files Biome doesn't recognize instead of erroring on them.
    "ignoreUnknown": true,
    // Scope Biome. Negated globs must follow a positive "**" match.
    // "!!" (double-bang) ALSO excludes from the project scanner used by
    // project-aware and type-aware rules — this is what you want for
    // build output and deps, to save a lot of CPU.
    "includes": [
      "**",
      "!!**/node_modules",
      "!!**/dist",
      "!!**/.output",
      "!!**/.nuxt",
      "!pnpm-lock.yaml"
    ]
  },

  "formatter": {
    "enabled": true,
    "indentStyle": "space",   // default: "tab"
    "indentWidth": 2,
    "lineWidth": 100,         // default: 80
    "lineEnding": "lf"
  },

  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
    // To force type-aware / project-wide rules, opt into a domain:
    // "domains": { "project": "recommended", "types": "recommended" }
    // (Both are expensive — they enable the module-graph scanner.)
  },

  "javascript": {
    "formatter": {
      "quoteStyle": "single",        // default: "double"
      "jsxQuoteStyle": "double",
      "semicolons": "asNeeded",      // default: "always"
      "trailingCommas": "all",
      "arrowParentheses": "always",
      "bracketSpacing": true,
      "bracketSameLine": false
    }
  },

  "json": {
    "formatter": {
      "trailingCommas": "none"
    }
  },

  // Enable Tailwind v4 `@theme` / `@apply` / etc. directive parsing.
  "css": {
    "parser": {
      "tailwindDirectives": true
    }
  },

  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  },

  // Per-glob overrides. `includes` here uses the same syntax as files.includes.
  "overrides": [
    {
      "includes": ["**/*.jsonc"],
      "json": {
        "parser": { "allowComments": true, "allowTrailingCommas": true },
        "formatter": { "trailingCommas": "none" }
      }
    }
  ]
}
```

### Config resolution

Biome searches in order: `biome.json` → `biome.jsonc` → `.biome.json` → `.biome.jsonc`. Starts in the current working directory, walks up, then falls back to the user's config dir (`$XDG_CONFIG_HOME/biome`, `~/Library/Application Support/biome`, `%APPDATA%\biome\config`). If nothing is found, defaults apply.

### Monorepos: nested configs

Use `extends` + `root: false` on each nested config:

```jsonc
// apps/web/biome.jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "extends": "//",   // v2 shorthand — "the root biome config in this project"
  "root": false,     // mark this as a nested (non-root) config
  "formatter": { "lineWidth": 120 }
}
```

`extends` can also take relative paths (`"../common.json"`) or a published package (`"@org/shared-configs/biome"` via `exports`).

See `references/configuration.md` for the complete config schema (every key, every option, every default).

## CLI essentials

```shell
# Day-to-day
biome check                    # format + lint + organize imports (read-only)
biome check --write            # apply safe fixes + formatting
biome check --write --unsafe   # also apply unsafe fixes (review diffs!)

# Targeted
biome format [--write] [paths...]
biome lint   [--write] [--unsafe] [paths...]
biome assist [--write] [paths...]

# VCS-scoped (needs vcs.enabled: true)
biome check --staged           # pre-commit: only git-staged files
biome check --changed          # only files changed vs. vcs.defaultBranch
biome check --since=main

# CI
biome ci                       # strict, no --write, auto GH annotations
biome ci --reporter=github
biome ci --reporter=junit --reporter-file=biome.junit.xml
biome ci --reporter=gitlab > code-quality.json

# Migration
biome migrate prettier --write
biome migrate eslint --write [--include-inspired]
biome migrate --write          # v1 → v2 config migration (after upgrade)

# Misc
biome init [--jsonc]
biome explain lint/suspicious/noExplicitAny
biome search '<GritQL pattern>'
biome rage                     # diagnostic dump for bug reports
biome start / biome stop       # daemon lifecycle (usually auto-managed)
biome lsp-proxy                # LSP over stdin/stdout (for editors)
```

Flag highlights:
- `--write` / `--fix` apply safe fixes and formatting (aliases)
- `--unsafe` additionally applies fixes flagged unsafe — behavior-changing rewrites like `==` → `===`
- `--only=<rule|group|domain|action>` / `--skip=…` focused runs; `--skip` wins over `--only`
- `--reporter=default|json|json-pretty|github|junit|summary|gitlab|checkstyle|rdjson|sarif` output format
- `--no-errors-on-unmatched` don't fail when the passed paths match nothing (critical for `--staged` in hooks)
- `--files-ignore-unknown=true` silently skip unknown file types
- `--max-diagnostics=<N>|none` cap diagnostics (default 20)
- `--error-on-warnings` promote warnings to failing
- `--stdin-file-path=<path>` format code from stdin, path determines language

Exit codes: `0` clean, `1` diagnostics/unsafe fixes needed, `2` CLI/config error, `101` fatal error.

Do **not** pass shell globs (`biome lint 'src/**/*.ts'`) — your shell expands them first, which is slow and loses Biome's own matching. Configure `files.includes` instead.

See `references/cli.md` for every subcommand and every flag.

## Linter

Rules are grouped by intent, each with its own default severity (`error`, `warn`, `info`, `off`). In v2, `style` rules default to **warn**, not error.

| Group | What it catches |
|---|---|
| `correctness` | Almost-certainly-bugs (unused vars, invalid regex, etc.) |
| `suspicious` | Looks wrong but sometimes intentional (`any`, `console.log`, `!=`) |
| `style` | Consistency (const vs let, import type, etc.) |
| `complexity` | Overwrought code (useless fragments, dead branches, excessive nesting) |
| `performance` | Slow patterns (`.forEach` in hot loops, barrel re-imports) |
| `security` | Obvious security footguns (`eval`, unsafe HTML) |
| `a11y` | Accessibility (missing alt text, unlabeled buttons) |
| `nursery` | New/experimental rules — names and behavior may change |

### Domains: framework-aware rule sets

Biome auto-detects framework dependencies in `package.json` and enables matching domains. You can also enable them explicitly:

```jsonc
{
  "linter": {
    "rules": { "recommended": true },
    "domains": {
      "react": "recommended",      // react ≥ 16
      "next": "recommended",       // next ≥ 14
      "vue": "recommended",        // vue ≥ 3
      "solid": "recommended",
      "qwik": "recommended",
      "test": "recommended",       // jest, vitest, mocha, ava
      "drizzle": "recommended",    // drizzle-orm ≥ 0.9
      "playwright": "recommended",
      "project": "recommended",    // expensive: module-graph scanner
      "types": "recommended"       // expensive: type inference
    }
  }
}
```

`project` and `types` are **expensive** — they build a module graph and infer types across the repo, adding seconds to every run for medium-to-large projects. Don't enable them unless you specifically want `noImportCycles`, `noUndeclaredDependencies`, `noFloatingPromises`, etc.

### Tuning rules

Keep `recommended: true` and override individual rules:

```jsonc
{
  "linter": {
    "rules": {
      "recommended": true,
      "style": {
        "useImportType": "error",
        "noNonNullAssertion": "off"
      },
      "suspicious": {
        "noExplicitAny": "warn"
      },
      "correctness": {
        "noUnusedVariables": {
          "level": "error",
          "fix": "none",      // "safe" | "unsafe" | "none" — controls what --write does
          "options": { }      // per-rule options, see rule docs
        }
      },
      "nursery": {
        "useSortedClasses": {
          "level": "warn",
          "options": { "functions": ["clsx", "cva", "cn", "tw"] }
        }
      }
    }
  }
}
```

### Suppressing diagnostics

Every suppression requires a reason — Biome enforces this:

```ts
// biome-ignore lint/suspicious/noExplicitAny: third-party types lie here
const foo: any = external()

// biome-ignore-all lint/suspicious/noExplicitAny: generated file (put at top of file)
```

For formatting:

```ts
// biome-ignore format: keep this table aligned by hand
const matrix = [
  1, 2, 3,
  4, 5, 6,
]
```

The category (`lint/...` or `format`) and the `: reason` are both mandatory.

### Safe vs. unsafe fixes

Each fix is labeled. `--write` applies only safe fixes; `--unsafe` also applies unsafe ones. Unsafe fixes may change runtime behavior (e.g., `==` → `===`, `let` → `const` when reassignment looks dead). Editor "fix on save" defaults to safe-only for the same reason. If a specific rule's safe fix is noisy (`noUnusedVariables` prefixing with `_`, for example), set `"fix": "none"` for that rule.

### Tailwind class sorting

`useSortedClasses` (nursery group, **unsafe** fix) sorts utility classes the same way `prettier-plugin-tailwindcss` does. It's not on by default. Caveats worth knowing: it only supports default Tailwind config (no custom utilities/variants from plugins), and it runs as a lint rule — not the formatter — so editor "format on save" will *not* apply it. Users have to run `biome check --write --unsafe` or wire the fix into a dedicated action.

See `references/linter.md` for rule groups in depth, common tuning recipes, and the noteworthy-rules cheatsheet.

## Assist

Assist actions sit between formatter and linter — safe source transformations. Configure each action individually:

```jsonc
{
  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "on",
        "useSortedKeys": "on",
        "useSortedAttributes": "on",
        "useSortedProperties": "on",
        "useSortedInterfaceMembers": "on"
      }
    }
  }
}
```

Values: `"on"`, `"off"`, or `{"level": "on", "options": {...}}`. Assist actions run under `biome check` and the standalone `biome assist`. They always emit safe fixes — if an assist action changes behavior, that's a Biome bug.

Editor code action identifiers:
- `source.fixAll.biome` — every safe fix (lint + assist)
- `source.organizeImports.biome` — just import sorting
- `source.action.<ACTION_NAME>.biome` — a specific assist action

## Language support snapshot

Stable: **JS, TS, JSX, TSX, JSON, JSONC, CSS, GraphQL**. HTML is supported but opt-in via `html.experimentalFullSupportEnabled: true`. **Vue, Svelte, Astro** are experimental (v2.3+) — JS/TS/CSS blocks inside get formatted and linted, but framework-specific template syntax isn't fully understood yet, so expect rough edges.

When linting `.vue`/`.svelte`/`.astro` without full HTML support, turn off rules that frequently false-positive:

```jsonc
{
  "overrides": [
    {
      "includes": ["**/*.svelte", "**/*.astro", "**/*.vue"],
      "linter": {
        "rules": {
          "style": { "useConst": "off", "useImportType": "off" },
          "correctness": { "noUnusedVariables": "off", "noUnusedImports": "off" }
        }
      }
    }
  ]
}
```

Not yet supported: **SCSS, YAML, Markdown** (parsers in progress; no linting yet).

See `references/framework-notes.md` for Vue / Svelte / Astro / React / Next / Tailwind / Nuxt specifics.

## Migration from Prettier + ESLint

Biome ships dedicated migration subcommands that rewrite your Biome config in place based on the old tools' configs:

```shell
biome migrate prettier --write
biome migrate eslint --write                    # strict equivalents only
biome migrate eslint --write --include-inspired # also port Biome rules "inspired by" ESLint
```

After migration:
1. Delete `.prettierrc*`, `.prettierignore`, `.eslintrc*`, `eslint.config.*`, `.eslintignore`.
2. Uninstall `prettier`, `eslint`, and every `prettier-plugin-*` / `eslint-plugin-*`.
3. Replace `prettier --write`, `eslint --fix`, etc. in `scripts` with `biome check --write`.
4. Update Husky / lint-staged / lefthook to call Biome.
5. In editor settings: make Biome the default formatter, disable the ESLint and Prettier extensions (or scope them away from paths Biome owns).

Gotchas:
- Biome's default indent is **tab** (Prettier's default is space). If you want to match Prettier, set `formatter.indentStyle: "space"`.
- `migrate eslint` disables `recommended: true` and emits an explicit rule list. Re-enable `recommended: true` manually if that's the behavior you want.
- Not every ESLint plugin has Biome equivalents — `migrate eslint` only handles TypeScript ESLint, React, JSX-A11y, Unicorn. For rules Biome doesn't have, consider GritQL plugins (`references/gritql.md`).
- `migrate eslint` doesn't parse YAML configs. Convert to JSON first.
- ESLint rules use `kebab-case`; Biome uses `camelCase`. When searching for a rule equivalent, look up the Biome rule sources page or try `biome explain`.

See `references/migration.md` for a step-by-step checklist and a mapping of common ESLint plugins to Biome equivalents.

## Integrations

### Editor

Install the official editor extension (VS Code: `biomejs.biome`; Zed: built-in; JetBrains: "Biome" plugin). In VS Code, set Biome as default formatter:

```jsonc
// .vscode/settings.json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit",
    "quickfix.biome": "explicit"
  },
  "[typescript]":       { "editor.defaultFormatter": "biomejs.biome" },
  "[typescriptreact]":  { "editor.defaultFormatter": "biomejs.biome" },
  "[javascript]":       { "editor.defaultFormatter": "biomejs.biome" },
  "[javascriptreact]":  { "editor.defaultFormatter": "biomejs.biome" },
  "[json]":             { "editor.defaultFormatter": "biomejs.biome" },
  "[jsonc]":            { "editor.defaultFormatter": "biomejs.biome" },
  "[css]":              { "editor.defaultFormatter": "biomejs.biome" },
  // Use Biome even when there's no biome.json in the project:
  "biomejs.requireConfiguration": false
}
```

Disable Prettier and ESLint extensions for files Biome handles so they don't fight.

### Git hooks

**lefthook** (zero-dep, recommended):

```yaml
# lefthook.yml
pre-commit:
  commands:
    biome:
      glob: "*.{js,ts,cjs,mjs,jsx,tsx,json,jsonc,css}"
      run: npx @biomejs/biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true
```

**lint-staged + husky**:

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts,cjs,mjs,jsx,tsx,json,jsonc,css}": [
      "biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"
    ]
  }
}
```

**pre-commit framework**:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/biomejs/pre-commit
    rev: v2.0.6
    hooks:
      - id: biome-check
        additional_dependencies: ["@biomejs/biome@2.4.13"]
```

`--no-errors-on-unmatched` is the key flag in all of these — without it, Biome exits non-zero when the staged-files list is empty after filtering.

### CI

Always use `biome ci` (not `biome check`) in CI. It's strictly read-only, knows how to talk to CI runners (GitHub annotations, JUnit, GitLab Code Quality, etc.), and supports `--changed` for PR-scoped runs.

**GitHub Actions** — use the first-party setup action:

```yaml
# .github/workflows/biome.yml
name: Code quality
on: { pull_request: {}, push: { branches: [main] } }
jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { persist-credentials: false, fetch-depth: 0 }
      - uses: biomejs/setup-biome@v2
        with: { version: latest }
      - run: biome ci .
```

`biome ci` emits GitHub annotations automatically when `GITHUB_ACTIONS=true` — no reporter flag needed. If your Biome config `extends` an npm package, install deps first (setup-node + `pnpm install`).

**Bitbucket Pipelines**:

```yaml
# bitbucket-pipelines.yml
image: node:22
pipelines:
  pull-requests:
    '**':
      - step:
          name: Biome
          caches: [node]
          script:
            - corepack enable && corepack prepare pnpm@latest --activate
            - pnpm install --frozen-lockfile
            - pnpm exec biome ci . --reporter=junit --reporter-file=biome.junit.xml
          artifacts:
            - biome.junit.xml
```

**GitLab CI** — emit the native Code Quality report format:

```yaml
# .gitlab-ci.yml
biome:
  image: node:22
  script:
    - corepack enable && corepack prepare pnpm@latest --activate
    - pnpm install --frozen-lockfile
    - pnpm exec biome ci . --reporter=gitlab --colors=off > gl-code-quality-report.json
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

**Everywhere else** — pick a reporter and save the output as a build artifact:

```shell
biome ci --reporter=junit --reporter-file=biome.junit.xml      # JUnit XML
biome ci --reporter=sarif > biome.sarif                         # SARIF for code-scanning dashboards
biome ci --reporter=checkstyle > biome.checkstyle.xml           # Checkstyle XML
```

**PR-scoped runs** (faster, only looks at changed files):

```shell
biome ci --changed --since=origin/main
```

Requires `vcs.enabled: true`, `vcs.defaultBranch`, and a deep git clone (`fetch-depth: 0` in GitHub Actions, `clone.depth: full` in Bitbucket).

See `references/recipes.md` for full CI snippets, Renovate, monorepo, and pre-commit patterns.

## Reference index

Load these when you need deeper coverage (they're chunked by topic so you only read what's relevant):

- `references/cli.md` — every subcommand, every flag, exit codes, env vars
- `references/configuration.md` — every `biome.json` key with types and defaults
- `references/linter.md` — rule groups, severity, options, noteworthy rules, domains, suppression patterns
- `references/migration.md` — step-by-step ESLint + Prettier migration checklist + v1→v2 breaking changes
- `references/framework-notes.md` — Vue, Svelte, Astro, React, Next, Tailwind, Nuxt specifics
- `references/recipes.md` — git hooks, CI, monorepo, Renovate, stdin usage, troubleshooting slowness

## Common gotchas

- **Tabs by default.** If you never set `formatter.indentStyle`, you'll get tabs. Teams coming from Prettier defaults will expect spaces.
- **`recommended: true` is a moving target.** Minor Biome versions can add rules. Pin the version (`-E`) so new warnings don't appear unannounced.
- **Suppression comments need a reason.** `// biome-ignore lint/suspicious/noExplicitAny` alone is a diagnostic; the trailing `: reason` is required.
- **Assist config moved in v2.** Older configs use `organizeImports.enabled` at the top level — that form is gone. It's now `assist.actions.source.organizeImports`.
- **Glob negation in `files.includes` must follow a positive match.** Start with `"**"`, then `"!…"` / `"!!…"`. Negated globs alone are ignored.
- **`--staged` needs `vcs.enabled: true`.** Otherwise Biome has no way to ask git what's staged.
- **Style rules default to `warn`, not `error`, in v2.** If you want them to fail CI, either set `"error-on-warnings"` or raise each rule's severity.
- **Vue/Svelte/Astro are experimental.** Expect a few rough edges; avoid aggressive auto-fix on commit for those files without review.
- **`biome migrate eslint` disables `recommended: true`.** It replaces it with an explicit rule list derived from your old config. Re-enable `recommended: true` manually if you want it.
- **Glob semantics changed in v2.** `*` no longer matches `/`; paths are resolved relative to the config file's directory (not CWD). Run `biome migrate --write` after upgrading from v1.
- **`project` and `types` domains are expensive.** They build a module graph / infer types across the whole repo. Only enable if you want the specific rules they unlock.
- **`files.maxSize` default is 1 MiB.** Large generated files are silently skipped. Raise it if needed.
