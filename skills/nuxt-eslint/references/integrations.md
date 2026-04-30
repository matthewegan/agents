# Integrations

Editor setup, Prettier, pre-commit hooks, CI, DevTools — the usual operational surface.

## Editor

### VS Code

Install extension: **ESLint** by Microsoft (`dbaeumer.vscode-eslint`).

```jsonc
// .vscode/settings.json
{
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  // ESLint extension < v3.0.10 needs this for flat config; v3.0.10+ is automatic:
  "eslint.useFlatConfig": true,
  // Validate these languages:
  "eslint.validate": [
    "javascript",
    "typescript",
    "vue"
  ]
}
```

For a Nuxt project that also uses Prettier, keep Prettier as the default formatter and let ESLint apply its `source.fixAll.eslint` action on save:

```jsonc
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

Order: Prettier formats on save, then ESLint applies auto-fixes. Both run on save.

### Recommended project extensions

```json
// .vscode/extensions.json
{ "recommendations": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "Vue.volar"] }
```

### Zed

```json
// .zed/settings.json
{
  "formatter": "prettier",
  "code_actions_on_format": { "source.fixAll.eslint": true }
}
```

### JetBrains (WebStorm, IntelliJ, etc.)

Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint:
- "Automatic ESLint configuration"
- Check "Run eslint --fix on save"

## Pairing with Prettier

Quickest, most common setup:

1. `pnpm add -D -E prettier`
2. Create `.prettierrc.json` and `.prettierignore` (see the `prettier` skill for templates)
3. Leave `config.stylistic: false` in `nuxt.config.ts` (that's the default)
4. Run both tools separately:
   - `eslint .` / `eslint . --fix` for code quality
   - `prettier . --write` / `prettier . --check` for formatting

No `eslint-config-prettier` needed because `@nuxt/eslint` doesn't enable formatting rules when stylistic is off.

If you DO enable stylistic rules AND want Prettier to own formatting:

```js
// eslint.config.mjs
import prettier from 'eslint-config-prettier'
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  prettier  // last — disables anything that conflicts with Prettier
)
```

Don't use `eslint-plugin-prettier` (it runs Prettier *through* ESLint — slow and noisy).

## Git hooks

### lefthook

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    eslint:
      glob: "*.{js,ts,tsx,jsx,vue}"
      run: npx eslint --fix --no-warn-ignored --max-warnings=0 {staged_files}
      stage_fixed: true
    prettier:
      glob: "*.{js,ts,tsx,jsx,vue,css,scss,html,json,jsonc,md,yaml,yml}"
      run: npx prettier --write --ignore-unknown {staged_files}
      stage_fixed: true
```

Install: `npx lefthook install`. On commit, staged JS/TS/Vue files run through ESLint + Prettier; fixed files are re-staged.

### husky + lint-staged

```json
// package.json
{
  "scripts": { "prepare": "husky" },
  "lint-staged": {
    "*.{js,ts,tsx,jsx,vue}": [
      "eslint --fix --no-warn-ignored --max-warnings=0"
    ],
    "*.{js,ts,tsx,jsx,vue,css,scss,html,json,jsonc,md,yaml,yml}": [
      "prettier --write --ignore-unknown"
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
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        files: \.(js|ts|vue|jsx|tsx)$
        args: ['--fix', '--max-warnings=0']
        additional_dependencies:
          - "eslint@^9"
          - "@nuxt/eslint@^1"
          - "typescript@^5"
```

(Version pins are examples — align with your project.)

## CI

### GitHub Actions

```yaml
name: Code quality
on: [pull_request, push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: 'pnpm' }
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec nuxt prepare   # required — generates .nuxt/eslint.config.mjs
      - run: pnpm exec eslint . --max-warnings=0 --report-unused-disable-directives --format=stylish
```

For JUnit output in CI (renders on PR Tests tabs), install `eslint-formatter-junit` as a devDep — ESLint 9 removed the built-in junit formatter:

```shell
pnpm add -D eslint-formatter-junit
```

The `nuxt prepare` step is important: `eslint.config.mjs` imports from `./.nuxt/eslint.config.mjs` which doesn't exist in a fresh clone until `nuxt prepare` runs.

Prettier step in parallel or serial:

```yaml
      - run: pnpm exec prettier . --check
```

### Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
image: node:22
definitions:
  steps:
    - step: &quality
        name: Code quality
        caches: [node, pnpm]
        script:
          - corepack enable && corepack prepare pnpm@latest --activate
          - pnpm install --frozen-lockfile
          - pnpm exec nuxt prepare
          - pnpm exec prettier . --check
          - mkdir -p test-results
          - pnpm exec eslint . --max-warnings=0 --format=junit -o test-results/eslint.junit.xml
        artifacts:
          - test-results/**
pipelines:
  pull-requests:
    '**':
      - step: *quality
```

Requires `eslint-formatter-junit` in devDependencies (ESLint 9 removed the built-in junit formatter).

Bitbucket auto-discovers test reports in these default paths (depth up to 3): `**/surefire-reports/**/*.xml`, `**/failsafe-reports/**/*.xml`, `**/test-results/**/*.xml`, `**/test-reports/**/*.xml`, `**/TestResults/**/*.xml`. Writing to the repo root (`eslint.junit.xml` alone) will **not** be discovered — use `test-results/eslint.junit.xml` (shown above) or declare a custom test-report artifact:

```yaml
artifacts:
  upload:
    - name: "eslint"
      type: "test-reports"
      paths:
        - "eslint.junit.xml"
```

The Tests tab only surfaces when there are failures — passing builds show nothing special, which is expected.

### GitLab CI

```yaml
quality:
  image: node:22
  script:
    - corepack enable && corepack prepare pnpm@latest --activate
    - pnpm install --frozen-lockfile
    - pnpm exec nuxt prepare
    - pnpm exec prettier . --check
    - pnpm exec eslint . --max-warnings=0 --format=junit -o eslint.junit.xml
  artifacts:
    when: always
    reports: { junit: eslint.junit.xml }
```

### Scoped PR runs

For faster CI on large monorepos, only lint files changed vs. the base branch:

```shell
git fetch origin "$BASE_BRANCH"
git diff "origin/$BASE_BRANCH"... --name-only --diff-filter=ACMR \
  | grep -E '\.(js|ts|tsx|jsx|vue)$' \
  | xargs -r pnpm exec eslint --max-warnings=0
```

Needs a deep clone (GitHub Actions: `fetch-depth: 0`; Bitbucket: `clone: { depth: full }`).

## Nuxt DevTools — Config Inspector

When `nuxt dev` is running and DevTools are enabled, there's an **ESLint** tab with a live Config Inspector. It shows:
- Every flat-config entry that makes up your resolved config, with names.
- Which files each entry applies to (via `files` globs).
- All rules that fire for a given file path.

Essential for debugging "why is this rule on/off for this file?" and for discovering the config names to `.override()` against. Also available CLI-only: `npx @eslint/config-inspector`.

## Renovate / dependency updates

Keep `eslint`, `@nuxt/eslint`, `typescript`, and your ESLint plugins all in one dependency group so Renovate opens a single PR that updates them in lockstep (otherwise you can end up with peer-dep mismatches).

```json
// renovate.json
{
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchPackageNames": ["eslint", "typescript"],
      "matchPackagePatterns": ["^@nuxt/eslint", "^@typescript-eslint/", "^eslint-plugin-"],
      "groupName": "eslint stack"
    }
  ]
}
```
