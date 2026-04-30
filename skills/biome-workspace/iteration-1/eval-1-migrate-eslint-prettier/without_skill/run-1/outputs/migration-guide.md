# Migrating a pnpm TypeScript Monorepo from ESLint + Prettier to Biome

End-to-end migration plan for a medium-sized TypeScript monorepo using pnpm workspaces. Assumes the starting state described:

- pnpm workspaces (`pnpm-workspace.yaml` at the repo root)
- Flat ESLint config (`eslint.config.js`) with `@typescript-eslint/eslint-plugin` and `eslint-plugin-unicorn`
- `.prettierrc.json` with 2-space indent, single quotes, trailing commas, 120-column line width
- Husky + lint-staged pre-commit hook

All commands below are meant to be run from the **repo root** unless stated otherwise. Biome is a single binary, so installing it once at the root is enough for the whole workspace.

---

## 1. Pre-flight

Before touching anything, make sure the working tree is clean and you have a branch to work on.

```bash
git status
git checkout -b chore/migrate-to-biome
```

Record the current "clean" baseline so you can diff formatting churn cleanly later:

```bash
pnpm -w exec eslint . --max-warnings=0 || true
pnpm -w exec prettier --check . || true
```

---

## 2. Install Biome

Install Biome as a single dev dependency at the workspace root. The `-w` flag tells pnpm to install it in the root `package.json`, which is what you want for a monorepo-wide tool.

```bash
pnpm add -Dw -E @biomejs/biome
```

Notes:
- `-E` pins the exact version. Biome rule sets evolve between minors; you want reproducible linting across machines and CI.
- Do **not** install Biome in each workspace package. One binary at the root runs against the whole tree.

Verify the install:

```bash
pnpm -w exec biome --version
```

---

## 3. Initialize `biome.json`

Create a Biome config by running the init command:

```bash
pnpm -w exec biome init
```

This writes `biome.json` at the repo root. Open it and update it to match your current Prettier settings (2-space indent, single quotes, trailing commas, 120-col width) and enable the recommended lint set. A config that mirrors your Prettier rules:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignoreUnknown": true,
    "ignore": [
      "**/dist/**",
      "**/build/**",
      "**/.next/**",
      "**/.turbo/**",
      "**/coverage/**",
      "**/node_modules/**",
      "**/*.snap",
      "**/pnpm-lock.yaml"
    ]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 120,
    "lineEnding": "lf"
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "jsxQuoteStyle": "double",
      "trailingCommas": "all",
      "semicolons": "always",
      "arrowParentheses": "always"
    }
  },
  "json": {
    "formatter": {
      "enabled": true,
      "trailingCommas": "none"
    }
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "organizeImports": {
    "enabled": true
  }
}
```

Key points:
- `vcs.useIgnoreFile: true` makes Biome honor `.gitignore` so you do not have to duplicate ignore patterns.
- `trailingCommas: "all"` matches Prettier's default `"trailingComma": "all"`.
- `quoteStyle: "single"` matches your `"singleQuote": true`.
- Biome writes `tsconfig.json` and `package.json` as JSON; turn on the JSON formatter or set per-file overrides if you care about those files.

If any workspace package needs a different config (rare), add a `biome.json` in that package directory — Biome walks upward and the nearest wins.

---

## 4. Migrate existing ESLint and Prettier config automatically

Biome ships migration commands that read your existing configs and translate overlapping options:

```bash
pnpm -w exec biome migrate eslint --write
pnpm -w exec biome migrate prettier --write
```

- `biome migrate eslint` reads `eslint.config.js` (flat config is supported) and ports the subset of rules that have Biome equivalents into `biome.json`.
- `biome migrate prettier` reads `.prettierrc.json` and writes matching formatter options into `biome.json`.

Review the diff afterward:

```bash
git diff biome.json
```

Expect partial coverage. Biome does not re-implement every `@typescript-eslint` or `unicorn` rule — see the Gotchas section for the concrete list to check.

---

## 5. Run Biome against the repo

Format and lint-fix in one pass:

```bash
pnpm -w exec biome check --write .
```

What this does:
- `check` runs formatter + linter + import organizer.
- `--write` applies safe fixes to disk.
- For unsafe fixes (rules flagged as potentially behavior-changing), run `biome check --write --unsafe .` — read the diff carefully before committing.

Commit the large mechanical reformatting in a **separate commit** from any config changes so reviewers can `git blame --ignore-rev` it:

```bash
git add -A
git commit -m "chore: apply biome formatting (mechanical)"
```

Then add the commit SHA to `.git-blame-ignore-revs`:

```bash
echo "<sha-of-the-reformatting-commit>" >> .git-blame-ignore-revs
git add .git-blame-ignore-revs
git commit -m "chore: ignore biome reformat in git blame"
```

And tell GitHub about it:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

---

## 6. Delete old config and ignore files

Remove every ESLint and Prettier artifact from the repo. From the root:

```bash
# Root-level config
rm -f eslint.config.js eslint.config.cjs eslint.config.mjs eslint.config.ts
rm -f .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json .eslintrc.yml .eslintrc.yaml
rm -f .eslintignore
rm -f .prettierrc .prettierrc.json .prettierrc.js .prettierrc.cjs .prettierrc.yaml .prettierrc.yml .prettierrc.toml prettier.config.js prettier.config.cjs
rm -f .prettierignore
```

Then sweep each workspace package for per-package overrides that may exist:

```bash
find packages apps -type f \( \
  -name '.eslintrc*' -o \
  -name 'eslint.config.*' -o \
  -name '.eslintignore' -o \
  -name '.prettierrc*' -o \
  -name 'prettier.config.*' -o \
  -name '.prettierignore' \
\) -print -delete
```

Adjust the roots (`packages apps`) to match your monorepo layout. Re-run `git status` and confirm only expected files were deleted.

Also check editor configs that reference the old tools:
- `.vscode/settings.json` — remove `"editor.defaultFormatter": "esbenp.prettier-vscode"` and any `"eslint.*"` entries; set `"editor.defaultFormatter": "biomejs.biome"` instead.
- `.vscode/extensions.json` — swap `esbenp.prettier-vscode` and `dbaeumer.vscode-eslint` for `biomejs.biome`.

---

## 7. Uninstall ESLint, Prettier, and their plugins

From the root workspace:

```bash
pnpm remove -w \
  eslint \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint-plugin-unicorn \
  eslint-config-prettier \
  eslint-plugin-prettier \
  prettier \
  @types/eslint \
  @types/eslint__js \
  typescript-eslint
```

If any of those are missing you will see a harmless "not found in dependencies" message. Add any other ESLint plugins you know you have (for example `eslint-plugin-import`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-plugin-n`, `eslint-plugin-promise`).

Now sweep each workspace package for leftover per-package dependencies. The `-r` flag makes pnpm recurse:

```bash
pnpm -r remove \
  eslint \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint-plugin-unicorn \
  eslint-config-prettier \
  eslint-plugin-prettier \
  prettier \
  typescript-eslint || true
```

Finally, regenerate the lockfile and prune:

```bash
pnpm install
pnpm store prune
```

Double-check that nothing in `node_modules` still references ESLint or Prettier at runtime:

```bash
grep -R --include=package.json -l '"eslint' . | grep -v node_modules
grep -R --include=package.json -l '"prettier' . | grep -v node_modules
```

Both greps should return no results.

---

## 8. Update `package.json` scripts

### Before

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check": "pnpm lint && pnpm format:check"
  }
}
```

### After

```json
{
  "scripts": {
    "lint": "biome lint .",
    "lint:fix": "biome lint --write .",
    "format": "biome format --write .",
    "format:check": "biome format .",
    "check": "biome check .",
    "check:fix": "biome check --write .",
    "ci": "biome ci ."
  }
}
```

Notes:
- `biome check` combines lint + format + import organize in one pass — use it as the default CI gate.
- `biome ci` is the CI-optimized variant: it never writes, emits GitHub-Actions-friendly annotations, and sets a non-zero exit on any diagnostic.
- If any individual workspace package has its own `lint` / `format` scripts in its `package.json`, delete them. Let the root script drive linting for the whole repo; Biome does not benefit from per-package invocations and running it per package will be slower.

---

## 9. Update the husky + lint-staged pre-commit hook

### Before — `.husky/pre-commit`

```sh
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm exec lint-staged
```

The hook itself does not need to change. The `lint-staged` config is what drives it.

### Before — `lint-staged` config (in root `package.json`)

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx,mjs,cjs}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml}": [
      "prettier --write"
    ]
  }
}
```

### After — `lint-staged` config

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx,mjs,cjs,json,jsonc}": [
      "biome check --write --no-errors-on-unmatched --files-ignore-unknown=true"
    ],
    "*.{md,yml,yaml}": []
  }
}
```

Important flags:
- `--no-errors-on-unmatched` — lint-staged passes a list of files; if none match Biome's supported types, do not fail.
- `--files-ignore-unknown=true` — skip file types Biome does not understand instead of erroring (JSON5, some edge extensions, etc.).
- Do **not** pass `--staged` here — lint-staged is already giving Biome only the staged files as argv. Using `--staged` on top of that double-handles and can silently skip files.

Biome does not format `.md`, `.yml`, or `.yaml`. If you want those formatted in pre-commit, keep a tiny Prettier install just for those — but the whole point of this migration is usually to remove Prettier, so the default above drops Markdown/YAML formatting from the hook. Bring it up with the team before finalizing.

Reinstall husky hooks so the shebang is correct on all dev machines:

```bash
pnpm exec husky
```

---

## 10. Update CI

Swap any `eslint` / `prettier --check` step for:

```yaml
- name: Lint and format check
  run: pnpm -w exec biome ci .
```

`biome ci` emits GitHub Actions annotations automatically, so failed checks show up inline on PRs. No extra action or reporter is needed.

If you use Turborepo or Nx, add a `lint` or `check` task that runs `biome ci .` from the root and mark it as a root-only task (do not fan out per package).

---

## 11. Verify

Run the full check locally before opening the PR:

```bash
pnpm -w exec biome ci .
pnpm -w -r exec tsc --noEmit
pnpm -w test
```

And stage a trivial change to confirm the pre-commit hook runs Biome:

```bash
touch scratch.ts && echo "const x: number = 1 ;" > scratch.ts
git add scratch.ts
git commit -m "test: hook"   # should auto-format scratch.ts
git reset HEAD~1 && rm scratch.ts
```

---

## Gotchas

Concrete things that bite during this exact migration. Read before you start.

1. **`eslint-plugin-unicorn` coverage is partial.** Biome's `recommended` set covers the big unicorn wins (no-array-for-each, prefer-node-protocol, throw-new-error, prefer-includes, etc.) but misses several. If you relied on `unicorn/filename-case`, `unicorn/no-null`, `unicorn/prevent-abbreviations`, or `unicorn/expiring-todo-comments`, there is no direct Biome equivalent. Decide whether to drop them or keep a minimal ESLint install just for those rules. Usually not worth it.

2. **`@typescript-eslint` type-aware rules are not available.** Biome is a pure-AST linter — it does not run the TypeScript type checker. Rules like `no-floating-promises`, `no-misused-promises`, `await-thenable`, `no-unsafe-assignment`, and `strict-boolean-expressions` have **no Biome equivalent**. If your team depended on these, you have two options: (a) keep a tiny ESLint install with `typescript-eslint` for those rules only, or (b) lean harder on `tsc --noEmit` in CI and accept the gap. Be honest with the team about which rules you are losing.

3. **Biome does not format Markdown, YAML, HTML, or CSS-in-JS.** Prettier did. If you had a habit of `pnpm format` tidying your docs, that stops working. Options: (a) leave docs alone, (b) keep Prettier as a doc-only dev dep scoped to `*.md,*.yml,*.yaml` (sad but valid), (c) use a different Markdown formatter like `markdownlint`.

4. **Import organization is a lint rule, not a separate tool.** Biome has `organizeImports` built in and it will reorder your imports on `biome check --write`. Expect a large diff on the first run. This is another reason to land the mechanical reformat as its own commit.

5. **Single-quote vs double-quote in JSX.** Biome defaults `jsxQuoteStyle` to `"double"` (matches Prettier). If your existing Prettier config set `"jsxSingleQuote": true`, set `javascript.formatter.jsxQuoteStyle: "single"` in `biome.json` or your JSX files will all get rewritten to double quotes.

6. **`trailingComma` vocabulary differs.** Prettier uses `"all" | "es5" | "none"`. Biome uses `trailingCommas: "all" | "es5" | "none"` (plural). The `biome migrate prettier` command handles this, but if you hand-edit, watch for the plural.

7. **`printWidth` is `lineWidth` in Biome.** Again, the migrator handles this. Hand edits must use `formatter.lineWidth`.

8. **`.prettierignore` and `.eslintignore` are not read.** Biome uses `.gitignore` (when `vcs.useIgnoreFile` is true) plus its own `files.ignore` array. Port any Prettier/ESLint-specific ignore patterns into `biome.json`'s `files.ignore` — do not assume they carry over.

9. **Per-package configs in a workspace.** Biome walks upward from the file being linted and uses the **nearest** `biome.json`. It does **not** merge parent + child configs. If you put a `biome.json` in one package, it fully replaces the root config for that package — copy the root settings you want to keep.

10. **VS Code users must install the Biome extension.** The `biomejs.biome` extension is what formats on save. `esbenp.prettier-vscode` and `dbaeumer.vscode-eslint` should be removed from `.vscode/extensions.json` or VS Code will keep complaining that Prettier/ESLint are missing. Add a workspace setting: `"editor.defaultFormatter": "biomejs.biome"` and per-language overrides if needed.

11. **`biome ci` vs `biome check` in CI.** Use `biome ci .` in CI, not `biome check .`. The `ci` variant disables cache, sets the CI reporter, and fails on any diagnostic including warnings. `biome check` has different default behavior and can let warnings through.

12. **Unsafe fixes.** `biome check --write` applies only safe fixes by default. Some valuable rules (e.g. `noUnusedImports`, `useOptionalChain`) require `--unsafe`. Run once with `--unsafe` locally, review the diff carefully, and commit. Do not put `--unsafe` in the pre-commit hook.

13. **`"type": "module"` interaction.** If a workspace package is `"type": "module"`, Biome's default `semicolons: "always"` and `quoteStyle: "single"` still apply — no change needed. But if you had Prettier per-package overrides keyed on ESM vs CJS, port those into `biome.json` overrides or a per-package `biome.json`.

14. **Husky v9 shape.** If you are on Husky v9, the hook file no longer sources `_/husky.sh`. The hook is just the command itself. If `pnpm exec husky` rewrites your hook and you had custom sourcing, re-verify the contents.

15. **Editor auto-fix on save can fight lint-staged.** If developers have format-on-save enabled via Biome, their files are already formatted by the time they stage. That is fine — Biome is idempotent — but if a dev disables the extension, pre-commit will start producing surprise reformats. Document the extension install in CONTRIBUTING.md.

16. **Biome versions and rule churn.** Pin the exact version (`-E` during install) and update deliberately. Minor releases add rules to the `recommended` set, which will break CI on the next `pnpm install` if you use a caret range. Upgrade in a dedicated PR.

17. **Generated files.** Ensure anything generated (Prisma client, GraphQL codegen, OpenAPI clients, `.next/`, `dist/`) is in `files.ignore` or `.gitignore`. First run of Biome against a forgotten generated directory can produce thousands of diagnostics.

18. **`pnpm install` after removing ESLint.** Some tooling (e.g. `create-t3-app` templates, `next lint`, CRA remnants) silently reinstalls ESLint as a transitive dep. After cleanup, grep `pnpm-lock.yaml` for `eslint` and `prettier` and trace where they come from:

    ```bash
    grep -nE "^\s+eslint" pnpm-lock.yaml | head
    pnpm why eslint
    pnpm why prettier
    ```

    If `next` is pulling `eslint`, that is fine (it is optional and only used by `next lint`, which you will stop calling).

19. **`next lint`.** If you are on Next.js and had `next lint` in scripts, delete it. Biome replaces it. Next 14+ supports custom linters; no extra config needed.

20. **CI caching.** If your old CI cached `~/.eslintcache` or a Prettier cache, remove those cache steps. Biome has its own cache and handles it transparently.
