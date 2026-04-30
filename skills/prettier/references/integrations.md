# Prettier integrations

ESLint pairing, editor setup, git hooks, CI, plugins, framework-specific notes.

## ESLint

### The modern pattern

1. **Prettier formats.** One tool. One command.
2. **ESLint lints.** Different tool. Different command.
3. Run both separately, not nested.

This is the consensus of the Prettier and ESLint teams as of recent years. Earlier patterns (running Prettier through ESLint via `eslint-plugin-prettier`) are discouraged — they're slow, noisy, and blur the tools' responsibilities.

### `eslint-config-prettier`

`eslint-config-prettier` is a preset that turns OFF every ESLint rule that conflicts with Prettier (things like `indent`, `quotes`, `semi`, `max-len`). Install it when your ESLint setup enables such rules:

```shell
pnpm add -D eslint-config-prettier
```

```js
// eslint.config.mjs (flat config)
import js from '@eslint/js'
import prettier from 'eslint-config-prettier'

export default [
  js.configs.recommended,
  // ...your other configs
  prettier,   // LAST — so it disables any rules earlier configs enabled
]
```

When you do NOT need it:
- `@nuxt/eslint` with default `config.stylistic: false` — stylistic rules are already off.
- ESLint configs that never enabled formatting rules in the first place.

When you DO need it:
- `@antfu/eslint-config` — enables stylistic rules by default.
- `airbnb-eslint-config` — enables `indent`, `quotes`, etc.
- Hand-rolled configs that include formatting rules.

### Don't use `eslint-plugin-prettier`

It runs Prettier as an ESLint rule. Every formatting diff surfaces as a lint error. Problems:
- Slow — ESLint re-runs Prettier per file, per rule check.
- Noisy — formatting issues show as red squiggles instead of auto-applied diffs.
- Mixes concerns — one tool doing two jobs.

Use two separate tools and two separate npm scripts. Clean.

### Running both in dev

Editor pattern:
- Prettier extension handles format-on-save.
- ESLint extension handles source.fixAll.eslint on save.
- Both run in parallel; Prettier's output is the final formatting.

CLI pattern:
```shell
pnpm format && pnpm lint:fix
```

CI pattern:
```shell
pnpm format:check
pnpm lint
```

## Editor

### VS Code

Install the official extension: **Prettier - Code formatter** (`esbenp.prettier-vscode`).

```jsonc
// .vscode/settings.json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.formatOnPaste": false,

  // Per-language defaults (optional — catches cases where a language
  // has a competing default formatter registered):
  "[javascript]":       { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[typescript]":       { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[javascriptreact]":  { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[typescriptreact]":  { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[vue]":              { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[json]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[jsonc]":            { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[css]":              { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[scss]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[html]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[markdown]":         { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[yaml]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[graphql]":          { "editor.defaultFormatter": "esbenp.prettier-vscode" }
}
```

Recommend the extension to contributors via `.vscode/extensions.json`:

```json
{ "recommendations": ["esbenp.prettier-vscode"] }
```

Gotcha: the extension uses the **project-local** Prettier (`node_modules/.bin/prettier`). If a developer has a globally installed Prettier of a different version, output might differ from the CLI. Pinning `prettier` exactly in `package.json` avoids this.

### JetBrains (WebStorm, IntelliJ, etc.)

Built-in. *Preferences / Settings → Languages & Frameworks → JavaScript → Prettier*:
- Check "Automatic Prettier configuration" (or select your config file manually).
- Check "Run on save" and "Run on reformat code".

### Zed

Prettier is the default formatter for supported languages in Zed. In `.zed/settings.json`:

```json
{
  "formatter": "prettier",
  "format_on_save": "on"
}
```

### Vim / Neovim

Several options — pick one:
- **`vim-prettier`** (`prettier/vim-prettier`) — Prettier-specific.
- **`conform.nvim`** (modern Neovim) — formatter framework with first-class Prettier support.
- **`null-ls.nvim`** / **`none-ls.nvim`** — exposes Prettier as an LSP source.
- **`coc-prettier`** — for coc.nvim users.

Configure format-on-save in your chosen plugin.

### Sublime Text

`JsPrettier` plugin via Package Control. Set "auto_format_on_save": true.

## Git hooks

### lint-staged + husky (most common)

Quickstart:

```shell
npx mrm@2 lint-staged
```

Auto-installs husky + lint-staged, configures `package.json`:

```json
{
  "scripts": { "prepare": "husky" },
  "lint-staged": {
    "**/*": "prettier --write --ignore-unknown"
  }
}
```

```sh
# .husky/pre-commit
#!/usr/bin/env sh
npx lint-staged
```

### lefthook (zero-dep, cross-platform)

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    prettier:
      glob: "*.{js,ts,tsx,jsx,vue,css,scss,html,json,jsonc,md,yaml,yml,graphql}"
      run: npx prettier --write --ignore-unknown {staged_files}
      stage_fixed: true
```

```shell
npx lefthook install
```

### pretty-quick

Runs Prettier only on files changed in git:

```shell
pnpm add -D pretty-quick simple-git-hooks
```

```json
// package.json
{
  "scripts": { "prepare": "simple-git-hooks" },
  "simple-git-hooks": {
    "pre-commit": "npx pretty-quick --staged"
  }
}
```

### Plain shell hook (no deps)

```sh
# .git/hooks/pre-commit
#!/bin/sh
FILES=$(git diff --cached --name-only --diff-filter=ACMR)
[ -z "$FILES" ] && exit 0

echo "$FILES" | xargs ./node_modules/.bin/prettier --ignore-unknown --write
echo "$FILES" | xargs git add
```

Remember `chmod +x .git/hooks/pre-commit`.

### Pre-commit framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        args: ['--ignore-unknown']
```

## CI

### GitHub Actions

```yaml
name: Format check
on: [pull_request, push]
jobs:
  prettier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: 'pnpm' }
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec prettier . --check
```

### Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
image: node:22
pipelines:
  pull-requests:
    '**':
      - step:
          name: Prettier
          caches: [node]
          script:
            - corepack enable && corepack prepare pnpm@latest --activate
            - pnpm install --frozen-lockfile
            - pnpm exec prettier . --check
```

### GitLab CI

```yaml
prettier:
  image: node:22
  script:
    - corepack enable && corepack prepare pnpm@latest --activate
    - pnpm install --frozen-lockfile
    - pnpm exec prettier . --check
```

## Plugins

Install + register in `.prettierrc.json`:

```json
{
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

Notable plugins:

### `prettier-plugin-tailwindcss`

Sorts Tailwind utility classes using the official Tailwind sort algorithm. Works on:
- `class="..."` in HTML, Vue templates, Astro, Svelte
- `className="..."` in JSX/TSX
- `cn(...)`, `clsx(...)`, `cva(...)`, `tw\`...\``, `twMerge(...)` and other helper functions

Configure custom helper functions:

```json
{
  "plugins": ["prettier-plugin-tailwindcss"],
  "tailwindFunctions": ["cn", "clsx", "cva", "twMerge", "tw"]
}
```

Integrates with a Tailwind config file (picked up automatically from `tailwind.config.*`).

**Plugin ordering:** if using with `prettier-plugin-organize-imports` or similar, `prettier-plugin-tailwindcss` should be **last** — its sort runs after other plugins.

### Framework plugins

- `prettier-plugin-svelte` — Svelte SFCs.
- `prettier-plugin-astro` — Astro files.
- `@prettier/plugin-pug` — Pug templates.

### Language plugins

- `@prettier/plugin-php` — PHP.
- `@prettier/plugin-ruby` — Ruby.
- `@prettier/plugin-xml` — XML.
- `prettier-plugin-sql` — SQL.
- `prettier-plugin-java` — Java.

### Utility plugins

- `prettier-plugin-organize-imports` — uses the TypeScript LSP's organize-imports action. Warning: reorders imports, which can be a behavior change if you have side-effect imports (`import 'some-lib/polyfill'`). Test carefully.
- `prettier-plugin-packagejson` — sorts `package.json` fields in a canonical order.
- `prettier-plugin-sort-json` — sorts JSON keys alphabetically.
- `prettier-plugin-embed` — formats embedded languages inside template literals more aggressively.

## Framework-specific notes

### Vue

Prettier splits a `.vue` file into sections:
- `<template>` — HTML parser.
- `<script>` / `<script setup>` — JS/TS parser per `lang`.
- `<style>` / `<style scoped>` — CSS/SCSS/Less parser per `lang`.

Key Vue option: `vueIndentScriptAndStyle` (default `false`). With `false`, contents of `<script>` and `<style>` start at column 0. With `true`, they're indented one level to match the SFC's visual hierarchy. Most style guides use `false`.

`singleAttributePerLine: true` is a useful pick for form-heavy templates.

### React / JSX

Standard config — nothing React-specific in Prettier. Common pairing:
- `jsxSingleQuote: false` (JSX attrs in double quotes — conventional).
- `singleQuote: true` (JS strings in single quotes).
- `bracketSameLine: false` (closing `>` on its own line — default).

### Svelte

Install `prettier-plugin-svelte`. Plugin options (set in `.prettierrc`):
- `svelteSortOrder` — component section ordering (e.g., `"scripts-markup-styles"`).
- `svelteStrictMode`, `svelteAllowShorthand`, `svelteIndentScriptAndStyle`.

### Astro

Install `prettier-plugin-astro`. Usually no extra config needed.

### Markdown

Key options:
- `proseWrap: "always"` for technical docs.
- `proseWrap: "preserve"` (default) for README-style.
- `printWidth: 80` for prose is a common pairing.

## Shared configs — publishing

See `sharing-configs.md` for publishing a shared `.prettierrc` as an npm package.
