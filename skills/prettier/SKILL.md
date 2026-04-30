---
name: prettier
description: "Prettier v3+ reference for opinionated code formatting across JavaScript, TypeScript, JSX/TSX, Vue, CSS, HTML, JSON, GraphQL, Markdown, YAML, and plugin-added languages. Use this skill whenever the user is installing, configuring, or troubleshooting Prettier — adding `prettier` to a project, writing or editing `.prettierrc*` / `prettier.config.*` / the `prettier` key in `package.json`, tuning Prettier options (printWidth, semi, singleQuote, trailingComma, arrowParens, vueIndentScriptAndStyle, etc.), managing `.prettierignore`, running `prettier . --write` / `prettier . --check`, integrating with ESLint, wiring up git hooks / CI / editor format-on-save, or pairing with plugins like `prettier-plugin-tailwindcss`. Also use whenever you see a `.prettierrc*` file or `prettier` in `package.json`, even if the user doesn't explicitly mention it."
---

# Prettier

Prettier is an **opinionated code formatter**. It reads source code and re-prints it to a canonical form — consistent line breaks, quotes, indentation, trailing commas. It is not a linter. It doesn't catch bugs or enforce rules about *what* code you write, only *how* it looks.

Current major version: **v3.x**. This skill targets v3. Key v3 changes vs v2: `trailingComma` default is now `"all"` (was `"es5"`), `endOfLine` default is `"lf"` (was `"auto"`).

## When to use this skill

- Adding Prettier to a project (fresh install)
- Writing or editing `.prettierrc`, `.prettierrc.json`, `.prettierrc.yaml`, `.prettierrc.js`, `prettier.config.js`, or the `"prettier"` key in `package.json`
- Tuning Prettier options or applying per-glob overrides
- Managing `.prettierignore`
- Running `prettier . --write` / `--check` / `--list-different`
- Integrating Prettier with ESLint (or another linter)
- Wiring up pre-commit hooks (husky + lint-staged, lefthook, pre-commit framework, pretty-quick)
- Configuring editors for format-on-save
- Enabling plugins (`prettier-plugin-tailwindcss`, `@prettier/plugin-php`, etc.)

## Mental model

- **Format, not lint.** Prettier decides whitespace, quotes, line breaks, trailing commas. It does NOT care about unused variables, dead code, `any`, React hooks rules — that's ESLint's job.
- **Opinionated, few options.** Prettier deliberately offers a small set of config options (~20) to stop teams from arguing. Common options tuned: `printWidth`, `semi`, `singleQuote`, `tabWidth`, `vueIndentScriptAndStyle`. The rest are usually fine at defaults.
- **Line width is a goal, not a hard limit.** `printWidth` (default 80) is the line length Prettier *prefers*. It will wrap earlier or later as needed to produce readable code. Don't expect rigid 80-column output.
- **Magic trailing commas.** A trailing comma in a multi-line array/object signals to Prettier: "keep this multi-line even if it could fit on one line." The opposite is true too — removing the trailing comma lets Prettier collapse short structures.
- **Prettier always overwrites with its own output.** Whatever formatting the source had is discarded on `--write`. This is why pinning the exact version matters: a minor Prettier upgrade can reshape every file in the repo.

## Installation

Install pinned with `--save-exact` (this matters — formatting output changes between versions):

```shell
# npm
npm install --save-dev --save-exact prettier

# pnpm
pnpm add -D -E prettier

# yarn
yarn add --dev --exact prettier

# bun
bun add -d --exact prettier
```

Why pinned: Prettier 3.0 → 3.1 can change how specific edge cases format. If every developer and CI pins the same version, you avoid churn; if they float, every machine re-formats files to slightly different shapes.

## Configuration

Config file formats, in the order Prettier searches:

1. `"prettier"` key in `package.json`
2. `.prettierrc` (JSON or YAML, auto-detected)
3. `.prettierrc.json` / `.prettierrc.json5`
4. `.prettierrc.yaml` / `.prettierrc.yml`
5. `.prettierrc.js` / `prettier.config.js`
6. `.prettierrc.mjs` / `prettier.config.mjs` (ES modules)
7. `.prettierrc.cjs` / `prettier.config.cjs` (CommonJS)
8. `.prettierrc.ts` / `prettier.config.ts` (Node 22.6+)
9. `.prettierrc.toml`

Discovery: Prettier walks upward from each file being formatted until it hits a config file OR a `package.json` (project root sentinel). Different subtrees can have different configs — a monorepo can put one `.prettierrc.json` per package.

### Canonical `.prettierrc.json`

Pick the settings that differ from defaults:

```json
{
  "printWidth": 100,
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "arrowParens": "always",
  "endOfLine": "lf",
  "vueIndentScriptAndStyle": false,
  "overrides": [
    {
      "files": "*.md",
      "options": { "printWidth": 80, "proseWrap": "always" }
    },
    {
      "files": ["*.yml", "*.yaml"],
      "options": { "singleQuote": false }
    }
  ]
}
```

### Default values (v3)

| Option | Default | Common overrides |
|---|---|---|
| `printWidth` | `80` | `100`, `120` |
| `tabWidth` | `2` | `4` |
| `useTabs` | `false` | — |
| `semi` | `true` | `false` (the "no-semi" style) |
| `singleQuote` | `false` | `true` |
| `jsxSingleQuote` | `false` | usually kept `false` even with `singleQuote: true` (JSX attrs → double) |
| `quoteProps` | `"as-needed"` | `"consistent"`, `"preserve"` |
| `trailingComma` | `"all"` | `"es5"` only for old ES5 targets; `"none"` almost never |
| `bracketSpacing` | `true` | — |
| `bracketSameLine` | `false` | `true` for compact HTML/JSX |
| `arrowParens` | `"always"` | `"avoid"` |
| `endOfLine` | `"lf"` | — (don't use `"auto"` — causes Windows churn) |
| `htmlWhitespaceSensitivity` | `"css"` | `"strict"`, `"ignore"` |
| `vueIndentScriptAndStyle` | `false` | `true` for aligned Vue SFC |
| `embeddedLanguageFormatting` | `"auto"` | `"off"` to disable inside template strings |
| `singleAttributePerLine` | `false` | `true` for vertical HTML attributes |
| `proseWrap` | `"preserve"` | `"always"`, `"never"` (Markdown) |

See `references/options.md` for every option, every value, and what it does.

### Overrides by glob

```json
{
  "semi": false,
  "overrides": [
    { "files": "*.test.js", "options": { "semi": true } },
    { "files": ["*.html", "legacy/**/*.js"], "options": { "tabWidth": 4 } }
  ]
}
```

`files` is a glob (or array of globs). `options` accepts any top-level Prettier option.

### `.editorconfig` interaction

If `.editorconfig` is present, Prettier reads it and maps supported properties (`indent_style`, `indent_size`, `end_of_line`, `max_line_length`, `insert_final_newline`) to Prettier options. Explicit `.prettierrc` settings win.

## `.prettierignore`

```text
# Build output
.nuxt
.output
.data
.nitro
.cache
dist
build
coverage

# Deps
node_modules

# Generated
**/*.generated.*

# Lockfiles
pnpm-lock.yaml
yarn.lock
package-lock.json
```

Important: **`.prettierignore` does NOT inherit from `.gitignore` automatically.** Many tools respect `.gitignore` by default; Prettier does not. Either:
- Maintain a `.prettierignore` explicitly (recommended).
- Use `--ignore-path .gitignore` on the CLI.

Prettier automatically skips `.git`, `.svn`, `.hg`, and `node_modules`.

Inline ignores:

```js
// prettier-ignore
const matrix = [1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1]
```

Markdown range ignore:

```markdown
<!-- prettier-ignore-start -->
| keep | this | table | as-is |
|------|------|-------|-------|
<!-- prettier-ignore-end -->
```

## CLI

```shell
prettier . --write          # format everything in place (destructive!)
prettier . --check          # check formatted; exit 1 if any file is unformatted
prettier . --list-different # print filenames that differ; exit 1 if any
prettier src/               # format just src/
prettier "src/**/*.ts"      # glob (quote to prevent shell expansion)
prettier --help
```

Common flags:

| Flag | Use |
|---|---|
| `--write` / `-w` | Overwrite files with formatted output |
| `--check` / `-c` | CI mode — exit 1 if unformatted |
| `--list-different` / `-l` | Print diff filenames; exit 1 if any |
| `--ignore-unknown` / `-u` | Silently skip files Prettier can't parse |
| `--ignore-path <file>` | Alternate ignore file (e.g. `.gitignore`) |
| `--config <path>` | Explicit config path |
| `--no-config` | Don't look for a config file |
| `--cache` | Cache results in `node_modules/.cache/prettier/` |
| `--log-level <level>` | `silent` / `error` / `warn` / `log` / `debug` |
| `--stdin-filepath <path>` | Read stdin, use path to infer parser |
| `--no-error-on-unmatched-pattern` | Don't fail when a glob matches nothing |

Exit codes: `0` clean, `1` unformatted files / failed check, `2` Prettier crash.

### `package.json` scripts

```json
{
  "scripts": {
    "format": "prettier . --write",
    "format:check": "prettier . --check"
  }
}
```

`format` is the dev command. `format:check` is the CI command.

See `references/cli.md` for every flag.

## Integration with ESLint

The only sensible modern pattern:

1. **Prettier formats.** Run `prettier --write` (locally, via format-on-save) or `prettier --check` (in CI).
2. **ESLint lints.** Run `eslint --fix` or `eslint --max-warnings=0`.
3. **Run them separately.** Don't nest Prettier inside ESLint.

### Avoid `eslint-plugin-prettier`

It runs Prettier as an ESLint rule, producing a red squiggle for every formatting diff. It's slow (ESLint reruns Prettier per file) and noisy. The modern consensus is to run Prettier and ESLint as separate steps.

### When you need `eslint-config-prettier`

`eslint-config-prettier` disables ESLint rules that overlap with Prettier's formatting (e.g. `indent`, `quotes`, `semi`). Add it as the **last** entry in your flat config so it overrides earlier ones.

- **With `@nuxt/eslint` defaults** (`config.stylistic: false`): you don't need `eslint-config-prettier`. The Nuxt module already ships with stylistic rules disabled.
- **With `@antfu/eslint-config` or presets that enable stylistic rules**: append `eslint-config-prettier`:

```js
// eslint.config.mjs
import js from '@eslint/js'
import prettier from 'eslint-config-prettier'

export default [
  js.configs.recommended,
  // ...your other config entries
  prettier,  // must be LAST
]
```

## Pre-commit hooks

### lint-staged + husky (most common)

```json
// package.json
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

`--ignore-unknown` makes Prettier silently skip files it doesn't understand (so staging a `*.log` or `*.env` doesn't fail the commit).

### lefthook

```yaml
# lefthook.yml
pre-commit:
  commands:
    prettier:
      glob: "*.{js,ts,tsx,jsx,vue,css,scss,html,json,jsonc,md,yaml,yml}"
      run: npx prettier --write --ignore-unknown {staged_files}
      stage_fixed: true
```

### pretty-quick

```json
{
  "scripts": { "prepare": "simple-git-hooks" },
  "simple-git-hooks": {
    "pre-commit": "npx pretty-quick --staged"
  }
}
```

Or just run `pretty-quick --staged` in your hook — it diffs git staging and runs Prettier on changed files.

See `references/integrations.md` for more hook patterns.

## CI

Simple pattern that works everywhere:

```shell
prettier . --check
```

Exit 1 if any file is unformatted. Fails the build; developer runs `prettier . --write` locally to fix.

**GitHub Actions:**

```yaml
name: Prettier
on: [pull_request, push]
jobs:
  prettier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx prettier . --check
```

**Bitbucket Pipelines / GitLab CI**: same idea — `prettier . --check` as the build step after `install`.

## Editor integration

### VS Code

```jsonc
// .vscode/settings.json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[javascript]":      { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[typescript]":      { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[typescriptreact]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[vue]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[json]":            { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[jsonc]":           { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[css]":             { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[html]":            { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[markdown]":        { "editor.defaultFormatter": "esbenp.prettier-vscode" }
}
```

Install the `esbenp.prettier-vscode` extension. It uses the project-local Prettier binary (not a global Prettier). If two developers have different local Prettier versions, they get different output — which is why you pin.

### JetBrains IDEs

Built-in. *Preferences → Languages & Frameworks → JavaScript → Prettier*. Enable "Run on save" and "Run on reformat code".

### Zed

Built-in. In `.zed/settings.json`:

```json
{ "formatter": "prettier" }
```

## Plugins

Prettier plugins add support for languages Prettier doesn't natively parse, or change formatting behavior. Install + register them in config:

```json
{
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

Notable plugins:
- **`prettier-plugin-tailwindcss`** — sorts Tailwind utility classes using the same algorithm as `eslint-plugin-tailwindcss`. Works in JSX, Vue templates, HTML. Common ask for any Tailwind project.
- **`@prettier/plugin-php`** — PHP formatting.
- **`@prettier/plugin-ruby`** — Ruby formatting.
- **`@prettier/plugin-pug`** — Pug templates.
- **`@prettier/plugin-xml`** — XML.
- **`prettier-plugin-svelte`** — Svelte SFCs (official Svelte plugin).
- **`prettier-plugin-astro`** — Astro files.
- **`prettier-plugin-organize-imports`** — uses the TypeScript LSP's organize-imports action (careful: reorders, which can introduce behavior changes with side-effect imports).
- **`prettier-plugin-sql`** — SQL formatting.

Plugin order matters when multiple plugins affect the same file — list them in the order you want them to run.

## Vue-specific behavior

Prettier formats `.vue` files section by section:
- `<template>` → HTML formatter
- `<script>` / `<script setup>` → JS/TS formatter (respects `lang` attribute)
- `<style>` → CSS/SCSS/Less formatter

Key Vue option:

```json
{ "vueIndentScriptAndStyle": false }  // default
```

With `false`, code inside `<script>` and `<style>` starts at column 0 (standard). With `true`, it's indented one level to match the SFC hierarchy. Most Vue style guides prefer the default.

`singleAttributePerLine: true` is a nicer choice for Vue templates with many attributes — one attribute per line instead of Prettier's default "wrap when over printWidth" heuristic.

See `references/integrations.md` for the full Vue section + framework-specific notes.

## Common gotchas

- **`--save-exact` matters.** Without it, `pnpm update` can pull in a new Prettier that reformats your entire repo overnight.
- **`.prettierignore` doesn't inherit from `.gitignore`.** Maintain both or pass `--ignore-path .gitignore`.
- **Default `trailingComma` is now `"all"` in v3.** If you're on ES5-only target or using a really old Node, drop to `"es5"`.
- **Default `endOfLine` is now `"lf"` in v3.** On Windows with `autocrlf=true`, you may see every file marked as modified after the first format. Fix with `.gitattributes: * text=auto eol=lf`.
- **Magic trailing commas drive wrapping.** A trailing comma in a multi-line literal asks Prettier to keep it multi-line; without it, short literals can collapse to a single line on next format.
- **`printWidth` is a soft target.** Prettier often wraps earlier or slightly later than the number suggests. Don't interpret it as a hard line-length rule.
- **Don't run Prettier on generated files / lockfiles.** Add them to `.prettierignore`. Formatting a lockfile can invalidate it.
- **Plugin updates don't bust Prettier's cache.** If a plugin upgrade changes output, delete `node_modules/.cache/prettier/` to force re-format.
- **Do NOT use `eslint-plugin-prettier`.** Run Prettier and ESLint as separate commands instead.

## Reference index

- `references/options.md` — every Prettier option, values, defaults, side effects
- `references/cli.md` — every CLI flag, usage recipes, exit codes
- `references/integrations.md` — ESLint pairing, editor setup, pre-commit hooks, CI snippets, plugin catalog, Vue/Astro/Svelte notes
- `references/sharing-configs.md` — publishing a shared Prettier config as an npm package
