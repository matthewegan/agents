# Migrating a pnpm TypeScript Monorepo from ESLint + Prettier to Biome

Target setup:

- pnpm workspaces monorepo
- Flat ESLint config (`eslint.config.js`) using `@typescript-eslint/eslint-plugin` + `eslint-plugin-unicorn`
- Prettier via `.prettierrc.json` (2-space indent, single quotes, trailing commas `all`, 120-col line width)
- Pre-commit: husky + lint-staged

End state:

- `@biomejs/biome` pinned at repo root as the single toolchain for format + lint + import organization
- One `biome.jsonc` at the repo root (optional nested overrides per workspace via `extends: "//"`)
- ESLint + Prettier + all their plugins uninstalled
- `package.json` scripts call `biome`
- husky + lint-staged run `biome check` on staged files

Do these steps in order. Each "Run" block lists the exact shell commands.

---

## Step 0 — Pre-flight

Commit anything pending so the migration diff is clean:

```shell
git status
git switch -c chore/biome-migration
```

Make sure you are at the **repo root** (where `pnpm-workspace.yaml` lives) for every command below. Biome should be installed once at the root — not per-package — so the whole monorepo shares one version and one config.

---

## Step 1 — Install Biome at the workspace root

```shell
pnpm add -D -E -w @biomejs/biome
```

Flag-by-flag:

- `-D` dev dependency
- `-E` pin exact version (Biome ships rule/format changes in patch releases — floating ranges cause surprise diffs)
- `-w` install to the workspace **root** `package.json`, not a child package

Generate a starter config as JSONC (preferred — you want comments next to non-default choices):

```shell
pnpm exec biome init --jsonc
```

This drops a `biome.jsonc` at the repo root. Leave it alone for now; the next step rewrites it based on your existing Prettier and ESLint config.

> Do **not** uninstall Prettier or ESLint yet — `biome migrate` needs to read their configs.

---

## Step 2 — Run the migration subcommands

Order matters: run Prettier first (it sets `formatter.*` keys), then ESLint (which populates `linter.*` without touching formatter):

```shell
pnpm exec biome migrate prettier --write
pnpm exec biome migrate eslint --write
```

Optional — also port Biome rules that are "inspired by" (not strict ports of) your ESLint plugin rules. This gives you better coverage of Unicorn and typescript-eslint rules that don't have exact Biome equivalents:

```shell
pnpm exec biome migrate eslint --write --include-inspired
```

Open `biome.jsonc` and sanity-check:

- `formatter.indentStyle` should be `"space"`, `indentWidth: 2`
- `formatter.lineWidth: 120`
- `javascript.formatter.quoteStyle: "single"`
- `javascript.formatter.trailingCommas: "all"`
- `javascript.formatter.semicolons` — set to whatever your Prettier had (`"always"` if `semi: true`, `"asNeeded"` if `semi: false`)

The ESLint migration disables `"recommended": true` and writes an explicit rule list derived from your old config. **If you'd rather keep Biome's recommended ruleset** and layer your overrides on top, manually set `"recommended": true` back and delete the rules it ported that simply duplicate the recommended defaults. (See Gotchas.)

Add the standard monorepo-friendly bits if they aren't already there. A good final shape:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  },
  "files": {
    "ignoreUnknown": true,
    "includes": [
      "**",
      "!!**/node_modules",
      "!!**/dist",
      "!!**/build",
      "!!**/.turbo",
      "!!**/coverage",
      "!pnpm-lock.yaml"
    ]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 120,
    "lineEnding": "lf"
  },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "jsxQuoteStyle": "double",
      "trailingCommas": "all",
      "semicolons": "always",
      "arrowParentheses": "always",
      "bracketSpacing": true
    }
  },
  "assist": {
    "enabled": true,
    "actions": {
      "source": { "organizeImports": "on" }
    }
  }
}
```

The `!!` (double-bang) excludes from **both** lint/format and the project scanner. Single `!` only excludes from lint/format but still indexes the files — `!!` is what you want for `node_modules`, `dist`, and build output.

### Optional: per-workspace overrides

If an individual package needs different rules (e.g. `packages/legacy-app` needs `noExplicitAny` off, or a tool package needs a 100-char line width), drop a nested config:

```jsonc
// packages/legacy-app/biome.jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "extends": "//",
  "root": false,
  "linter": {
    "rules": {
      "suspicious": { "noExplicitAny": "off" }
    }
  }
}
```

`extends: "//"` means "the root Biome config in this project." `root: false` marks it as a nested config. A single `biome ci .` at the repo root walks every package and honors each nested file.

---

## Step 3 — Delete the old config files

```shell
rm -f .prettierrc .prettierrc.json .prettierrc.js .prettierrc.cjs .prettierrc.mjs \
      .prettierrc.yml .prettierrc.yaml .prettierrc.toml \
      prettier.config.js prettier.config.cjs prettier.config.mjs prettier.config.ts \
      .prettierignore
rm -f .eslintrc .eslintrc.json .eslintrc.js .eslintrc.cjs .eslintrc.yml .eslintrc.yaml \
      eslint.config.js eslint.config.cjs eslint.config.mjs eslint.config.ts \
      .eslintignore
```

Also check each workspace package — flat ESLint projects sometimes ship a per-package `eslint.config.js` or a `.prettierrc` override:

```shell
find packages apps -maxdepth 2 \( \
  -name '.prettierrc*' -o -name 'prettier.config.*' -o -name '.prettierignore' \
  -o -name '.eslintrc*' -o -name 'eslint.config.*' -o -name '.eslintignore' \
\) -print -delete
```

(Adjust `packages apps` to whatever top-level workspace directories you actually use — check your `pnpm-workspace.yaml`.)

Commit this step on its own so the diff is easy to review.

---

## Step 4 — Uninstall ESLint, Prettier, and every plugin

Remove from the **root** `package.json` (where these typically live in a flat-config monorepo):

```shell
pnpm remove -w \
  eslint \
  prettier \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint-plugin-unicorn \
  @eslint/js \
  typescript-eslint
```

(The last two are common transitive companions under flat config — drop them if present.)

Catch any other `eslint-*`, `eslint-plugin-*`, `eslint-config-*`, `@typescript-eslint/*`, or `prettier-plugin-*` packages that might be lingering:

```shell
# Preview what would be removed (dry run) — from the repo root
jq -r '
  (.devDependencies // {}) + (.dependencies // {})
  | keys[]
  | select(
      . == "eslint" or . == "prettier"
      or startswith("eslint-")
      or startswith("@typescript-eslint/")
      or startswith("prettier-plugin-")
      or startswith("eslint-config-")
      or startswith("eslint-plugin-")
    )
' package.json
```

Then remove them:

```shell
pnpm remove -w $(jq -r '
  (.devDependencies // {}) + (.dependencies // {})
  | keys[]
  | select(
      . == "eslint" or . == "prettier"
      or startswith("eslint-") or startswith("@typescript-eslint/")
      or startswith("prettier-plugin-") or startswith("eslint-config-")
      or startswith("eslint-plugin-")
    )
' package.json | tr '\n' ' ')
```

Repeat the same check inside each workspace package that has its own `devDependencies` — in a pnpm monorepo plugins sometimes live per-package:

```shell
for pkg in packages/* apps/*; do
  if [ -f "$pkg/package.json" ]; then
    deps=$(jq -r '
      (.devDependencies // {}) + (.dependencies // {})
      | keys[]
      | select(
          . == "eslint" or . == "prettier"
          or startswith("eslint-") or startswith("@typescript-eslint/")
          or startswith("prettier-plugin-") or startswith("eslint-config-")
          or startswith("eslint-plugin-")
        )
    ' "$pkg/package.json" | tr '\n' ' ')
    if [ -n "$deps" ]; then
      (cd "$pkg" && pnpm remove $deps)
    fi
  fi
done
```

Finally, re-lock:

```shell
pnpm install
```

Verify nothing ESLint/Prettier-shaped is still in the lockfile:

```shell
grep -E '(^|/)(eslint|prettier|@typescript-eslint)' pnpm-lock.yaml | head -20
```

(A few transitive hits are fine if they're dependencies of something else — e.g. Storybook or vite plugins may pull `prettier` transitively. The goal is no direct entries in any `package.json`.)

---

## Step 5 — Update `package.json` scripts

### Before

```json
{
  "scripts": {
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

### After

```json
{
  "scripts": {
    "format": "biome format --write",
    "format:check": "biome format",
    "lint": "biome lint",
    "lint:fix": "biome lint --write",
    "check": "biome check",
    "check:fix": "biome check --write",
    "ci": "biome ci"
  }
}
```

Notes:

- `biome check` runs formatter + linter + import organize in one pass. It's the normal dev command.
- `biome ci` is the CI command — strictly read-only, auto-emits GitHub annotations when `GITHUB_ACTIONS=true`. **Never pass `--write` to `biome ci`** (it rejects the flag), and **never run `biome check --write` in CI**.
- No shell globs. Don't write `biome check 'src/**/*.ts'` — let Biome do the matching via `files.includes`.

If individual workspace packages had their own `lint`/`format` scripts calling ESLint/Prettier directly, delete them. With a single root `biome.jsonc`, one root-level `pnpm lint` covers the whole repo. Only keep per-package scripts if you genuinely want to lint one workspace at a time, in which case:

```json
{
  "scripts": {
    "lint": "biome lint .",
    "check": "biome check ."
  }
}
```

---

## Step 6 — Update husky + lint-staged

### Before — `package.json`

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml,css}": [
      "prettier --write"
    ]
  }
}
```

### After — `package.json`

```json
{
  "lint-staged": {
    "*.{js,ts,cjs,mjs,jsx,tsx,json,jsonc,css}": [
      "biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"
    ]
  }
}
```

Key flags:

- `--write` apply safe fixes and formatting
- `--no-errors-on-unmatched` don't fail the commit when the filtered staged list is empty
- `--files-ignore-unknown=true` silently skip file types Biome doesn't handle (Markdown, YAML, etc.)

Drop Markdown, YAML, and SCSS from the lint-staged glob — **Biome doesn't format any of those as of v2**. If you want them formatted, keep a minimal Prettier install scoped to just those extensions (but that defeats most of the point of this migration; usually easier to live without).

### Husky hook — unchanged

`.husky/pre-commit` should already be:

```sh
#!/usr/bin/env sh
npx lint-staged
```

If it directly invoked `eslint` or `prettier`, replace with the above. No other husky changes needed.

### Why not `biome check --staged` in the hook?

`--staged` works and is in fact faster when your staged set is large, but lint-staged gives you:

- per-file parallelism
- automatic re-staging of fixed files
- a single consistent pre-commit tool for non-Biome steps (e.g. if you later add a typecheck command)

Stick with lint-staged unless you want to drop it entirely and call `biome check --staged --write --no-errors-on-unmatched` from the hook.

---

## Step 7 — First run + triage

```shell
pnpm exec biome check .
```

Almost always produces a wall of diagnostics on first run. Apply safe fixes:

```shell
pnpm exec biome check --write .
```

Review the diff. Then — and only then — apply unsafe fixes (behavior-changing rewrites like `==` → `===`, dead `let` → `const`):

```shell
pnpm exec biome check --write --unsafe .
```

Commit the format/safe-fix pass separately from the unsafe pass so reviewers can distinguish "cosmetic" from "possibly behavioral."

For anything remaining:

- Pick rules that produce too much noise to fix now and demote them in `biome.jsonc`:
  ```jsonc
  "linter": {
    "rules": {
      "recommended": true,
      "suspicious": { "noExplicitAny": "warn" },
      "style":      { "noNonNullAssertion": "off" }
    }
  }
  ```
- Suppress a single line with a reason (Biome **requires** the reason):
  ```ts
  // biome-ignore lint/suspicious/noExplicitAny: third-party types lie here
  const x: any = external();
  ```
- For whole-file suppression at the top:
  ```ts
  // biome-ignore-all lint/suspicious/noExplicitAny: generated file
  ```

---

## Step 8 — Update CI

Replace your current ESLint/Prettier CI job with one `biome ci` call. GitHub Actions example:

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
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec biome ci .
```

`biome ci` auto-detects `GITHUB_ACTIONS=true` and emits inline annotations. No reporter flag needed.

---

## Step 9 — Update editor settings

Commit a `.vscode/settings.json` so the whole team gets the same behavior:

```jsonc
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
  "[css]":             { "editor.defaultFormatter": "biomejs.biome" }
}
```

And recommend the extension:

```json
// .vscode/extensions.json
{ "recommendations": ["biomejs.biome"] }
```

Tell the team to **disable** the Prettier and ESLint VS Code extensions (globally, or at least for this workspace) so they don't fight format-on-save with Biome.

---

## Gotchas

Concrete items to watch for during and after the migration.

### Config gotchas

- **Biome's default indent is tab, not space.** If you skip `biome migrate prettier`, you'll get tabs even though your Prettier was spaces. The migrate command sets `indentStyle: "space"` for you; if you hand-write the config, don't forget it.
- **`biome migrate eslint` sets `recommended: false`.** It writes an explicit, flat list of ported rules. If you wanted Biome's recommended ruleset *plus* your overrides, manually flip `"recommended": true` back on after migration — and then delete the explicit entries that just duplicate recommended.
- **`style` rules default to `warn`, not `error` in v2.** Your CI will stay green even with style violations. If you want them to fail CI, either set `"error-on-warnings"` on the CI command, or raise individual rule severities in `biome.jsonc`.
- **Glob negation must follow a positive match.** In `files.includes`, start with `"**"` then add `"!…"` / `"!!…"` entries. A config that starts with a `!` alone silently ignores it.
- **`*` does not match `/` in Biome v2.** Use `**` for recursion. Paths in `includes` resolve relative to the **config file's directory**, not CWD.
- **`--staged` needs `vcs.enabled: true`.** Otherwise Biome has no way to ask git what's staged. Same for `--changed`.
- **Suppression comments require a reason.** `// biome-ignore lint/suspicious/noExplicitAny` on its own is a diagnostic. Always add `: reason`.

### Coverage gaps vs. ESLint + Prettier

- **Biome doesn't format Markdown, YAML, or SCSS.** If Prettier was handling these, they're orphaned after the migration. Options: (1) live without it, (2) keep a minimal Prettier install scoped to just those extensions via a separate lint-staged entry, (3) wait for Biome's roadmap.
- **Not every `eslint-plugin-unicorn` rule has a Biome equivalent.** `biome migrate eslint --include-inspired` ports the close-enough Biome rules, but some Unicorn checks (e.g. `prefer-top-level-await`, `no-array-callback-reference`) have no counterpart. Either live without them or write a GritQL plugin. Run `biome explain lint/<group>/<rule>` to see what's available.
- **`@typescript-eslint` type-aware rules are opt-in and expensive.** Rules like `no-floating-promises` live in Biome's `types` domain, which builds a type-inference graph across the whole repo — seconds of overhead per run. Enable only if you specifically need them:
  ```jsonc
  "linter": { "domains": { "types": "recommended" } }
  ```
- **No direct equivalent for custom ESLint rules.** If your team has hand-rolled ESLint rules, they don't port. Use GritQL if the rule is important.
- **ESLint rules are `kebab-case`; Biome rules are `camelCase`.** When searching for the Biome equivalent of `@typescript-eslint/no-explicit-any`, look up `noExplicitAny`.

### Workflow gotchas

- **Prettier/ESLint may be transitive dependencies of other tools** (Storybook, vite plugins, `@typescript-eslint/utils` consumers). They may linger in `pnpm-lock.yaml` after you uninstall the direct deps — that's fine, as long as no `package.json` lists them directly.
- **First run will be noisy.** Biome's `noExplicitAny`, `noNonNullAssertion`, `useImportType`, `useConst`, `noUnusedVariables` are commonly stricter than typical ESLint configs. Budget a day to either fix or demote.
- **`biome check --write` and `biome check --write --unsafe` are two separate passes.** Commit them separately. Unsafe fixes can change runtime behavior (e.g., `==` → `===`, `let` → `const` when reassignment appears dead).
- **Editor "format on save" only applies safe fixes.** If you have a rule whose safe fix is annoying (e.g. `noUnusedVariables` prefixes unused args with `_`), set `"fix": "none"` on that rule.
- **Don't pass shell globs to the Biome CLI.** `biome lint 'src/**/*.ts'` gets expanded by your shell before Biome sees it — slow and bypasses Biome's own ignore logic. Use `files.includes` in config instead.
- **Biome is a single pinned version per repo.** If one of your workspace packages had its own ESLint version in a pre-migration world, you lose that isolation — now everyone shares the root's pinned Biome. Usually a feature, but worth calling out.
- **`package.json` expands by default in v2.** Biome will re-expand collapsed `package.json` forms. If your old Prettier left them collapsed and the churn bothers you, add an override:
  ```jsonc
  "overrides": [
    {
      "includes": ["**/package.json"],
      "json": { "formatter": { "expand": "auto" } }
    }
  ]
  ```
- **`pnpm-lock.yaml` is protected.** Biome never emits diagnostics for lockfiles, so no `!pnpm-lock.yaml` entry is strictly required — but adding it makes intent explicit.
- **Renovate / Dependabot version bumps.** Because Biome ships formatter/rule changes in patch releases, a Renovate bump can produce large diffs the next time someone saves a file. Pair Biome version bumps with a `biome check --write` pass in the same PR, and keep the `$schema` URL's version in sync. See the `recipes.md` Renovate snippet.

### CI gotchas

- **`fetch-depth: 0` (full clone) is required** if you want `biome ci --changed --since=origin/main` in CI. Shallow clones can't diff against the base branch.
- **`biome ci` rejects `--write`.** If you copy-paste a dev command into CI, you'll get a CLI error (exit 2). Use `biome ci` bare in CI.
- **No `biome ci` in pre-commit.** It's the slow, strict runner — use `biome check --staged --write` (or lint-staged running `biome check --write`) in hooks.

---

## Quick reference — end-to-end command sequence

For a clean run, this is the minimum sequence:

```shell
# 1. Install
pnpm add -D -E -w @biomejs/biome
pnpm exec biome init --jsonc

# 2. Migrate config
pnpm exec biome migrate prettier --write
pnpm exec biome migrate eslint --write --include-inspired

# 3. Delete old configs (root)
rm -f .prettierrc .prettierrc.json .prettierignore \
      eslint.config.js eslint.config.mjs .eslintignore

# 3b. Delete old configs (per-workspace)
find packages apps -maxdepth 2 \( \
  -name '.prettierrc*' -o -name 'prettier.config.*' -o -name '.prettierignore' \
  -o -name '.eslintrc*' -o -name 'eslint.config.*' -o -name '.eslintignore' \
\) -delete

# 4. Uninstall packages
pnpm remove -w eslint prettier \
  @typescript-eslint/eslint-plugin @typescript-eslint/parser \
  eslint-plugin-unicorn typescript-eslint @eslint/js
pnpm install

# 5. Update scripts and lint-staged (manual edits to package.json)

# 6. First run
pnpm exec biome check --write .
pnpm exec biome check .        # see what's left, tune biome.jsonc

# 7. Commit
git add -A
git commit -m "chore: replace eslint + prettier with biome"
```
