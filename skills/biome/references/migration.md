# Migration reference

Two migrations, often done at once: **Prettier + ESLint → Biome** (the common case), and **Biome v1 → v2** (upgrading an existing Biome setup).

## Prettier + ESLint → Biome

### Step 1 — install Biome

```shell
pnpm add -D -E @biomejs/biome    # or npm/yarn/bun equivalents; see SKILL.md
pnpm exec biome init --jsonc     # creates biome.jsonc
```

Don't uninstall Prettier/ESLint yet — the migration subcommands need to read their configs.

### Step 2 — run migration

```shell
# Order matters if you run both: do Prettier first (it sets formatter.* keys),
# then ESLint (it sets linter.* keys without touching formatter).
pnpm exec biome migrate prettier --write
pnpm exec biome migrate eslint --write
# Optional: also port Biome rules "inspired by" ESLint rules, not just strict ports
pnpm exec biome migrate eslint --write --include-inspired
```

What gets ported:
- Prettier: `useTabs`, `singleQuote`, `tabWidth`, `semi`, `trailingComma`, `printWidth`, `bracketSpacing`, `jsxSingleQuote`, `arrowParens`, per-file overrides.
- ESLint: extends chain, plugin rules from TypeScript ESLint / JSX-A11y / React / Unicorn, globals, `overrides`, `.eslintignore`.

### Step 3 — clean up

```shell
# Remove old configs
rm -f .prettierrc .prettierrc.json .prettierrc.js .prettierrc.yml .prettierrc.yaml
rm -f .prettierignore prettier.config.js prettier.config.ts
rm -f .eslintrc .eslintrc.json .eslintrc.js .eslintrc.yml
rm -f eslint.config.js eslint.config.ts eslint.config.mjs
rm -f .eslintignore

# Remove packages
pnpm remove prettier eslint \
  $(jq -r '.devDependencies | keys[] | select(startswith("eslint-") or startswith("@typescript-eslint/") or startswith("prettier-plugin-"))' package.json | xargs)
```

### Step 4 — update `package.json` scripts

Before:
```json
{
  "scripts": {
    "format": "prettier --write .",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

After:
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

### Step 5 — update hooks

`lint-staged` / Husky / lefthook entries that called `prettier` or `eslint` should now call `biome check --write --no-errors-on-unmatched --files-ignore-unknown=true`. See `recipes.md`.

### Step 6 — update editors

- VS Code: install `biomejs.biome`. Set `"editor.defaultFormatter": "biomejs.biome"`. Disable the Prettier and ESLint extensions for the paths Biome owns (or globally, if Biome owns everything).
- Zed: built-in support; just set `"formatter": "biome"` in `.zed/settings.json`.
- JetBrains: install the "Biome" plugin.

### Step 7 — re-check and re-tune

```shell
pnpm exec biome check .
```

Expect the first run to surface violations that didn't exist in your old setup:

- Biome's `noExplicitAny`, `noNonNullAssertion`, `useImportType`, `useConst`, `noUnusedVariables` are commonly absent or weaker in typical ESLint configs. Demote to `"warn"` or `"off"` if the backlog is too large to fix in one sweep (see `linter.md` § "Common tuning recipes").
- If `migrate eslint` set `recommended: false` and you actually wanted recommended rules + your old overrides, restore `"recommended": true` manually and keep the explicit rules it wrote.

### Things `biome migrate eslint` doesn't handle

- YAML `eslint.config.yaml` / `.eslintrc.yaml`. Convert to JSON first.
- Custom ESLint plugins or rules that have no Biome equivalent. Either live without them, or implement the missing check with a GritQL plugin.
- Rules whose semantics differ too much (plugin-authored `eqeqeq` variants, etc.). `--include-inspired` covers the "close enough" rules; otherwise expect gaps.
- Cyclic plugin/extends chains — Biome bails on those.

### Default differences to expect

| Setting | Prettier default | Biome default | If you want to match Prettier |
|---|---|---|---|
| Indent | space | **tab** | `formatter.indentStyle: "space"` |
| Trailing comma | `"all"` | `"all"` | — |
| Single quotes | `false` | — | `javascript.formatter.quoteStyle: "single"` |
| Semicolons | `true` | `"always"` | — |
| Line width | 80 | 80 | — |
| `package.json` expansion | auto | **always** | add override with `json.formatter.expand: "auto"` |

## Biome v1 → v2

Biome v2 is a substantial rework. Use the built-in migrator:

```shell
pnpm add -D -E @biomejs/biome@^2
pnpm exec biome migrate --write
```

What `biome migrate --write` does:
- Renames `rome.json` → `biome.json` if still present (historical).
- Updates the schema URL in `$schema`.
- Merges `ignore` + `include` fields into `includes` (with new glob semantics).
- Moves `organizeImports` from top-level → `assist.actions.source.organizeImports`.
- Updates suppression syntax comments where it can (`// rome-ignore` → `// biome-ignore`, and `biome-ignore lint(group/rule):` → `biome-ignore lint/group/rule:`).

### Breaking changes you need to know about

1. **Glob engine rewrite.** `*` no longer matches `/` — use `**` for recursion. Globs are no longer auto-prefixed with `**/`. Paths resolve relative to the config file's directory, not to the CWD.
2. **Suppression syntax.** v1: `// biome-ignore lint(suspicious/noExplicitAny): reason`. v2: `// biome-ignore lint/suspicious/noExplicitAny: reason`.
3. **Import organization moved.** v1: top-level `"organizeImports": { "enabled": true }`. v2: `"assist": { "actions": { "source": { "organizeImports": "on" } } }`.
4. **`style` rules default to `warn`.** In v1 recommended style rules were errors. If you want the v1 behavior, set `style` to `"error"` at the group level or raise individual rules.
5. **`"all": true` shortcut removed.** There's no single switch to enable every rule. Use `recommended: true` + domain configs or list rules explicitly.
6. **Attribute import syntax.** `import … assert { type: "json" }` → `import … with { type: "json" }`. Only the `with` form is supported now.
7. **`--config-path` removed from `start` / `lsp-proxy`.** Use `BIOME_CONFIG_PATH` env var or rely on default resolution.
8. **`package.json` default expansion is `"always"`.** If you liked the v1 compact form, add an override: `{ "includes": ["**/package.json"], "json": { "formatter": { "expand": "auto" } } }`.

### Post-upgrade sanity check

```shell
pnpm exec biome check .     # read-only
pnpm exec biome ci .        # the stricter runner
```

Review the diff output carefully — the re-formatter will repaint any file whose output changed vs. the v1 formatter, and there will be some (package.json expansion most commonly).
