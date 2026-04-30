---
name: nuxt-eslint
description: "@nuxt/eslint v1 module reference for adding ESLint to Nuxt 3/4 projects — flat config, Vue + TypeScript + Nuxt-aware rules, auto-generated `eslint.config.mjs`, and optional ESLint Stylistic / dev-server checker. Use this skill whenever the user is setting up, configuring, or troubleshooting ESLint in a Nuxt project — installing `@nuxt/eslint`, editing `eslint.config.mjs`, tuning rules via `withNuxt()`, configuring the module via `nuxt.config.ts`, enabling `config.stylistic` or `config.checker`, integrating with Prettier, migrating from `@nuxtjs/eslint-module` or legacy `.eslintrc`, or running `eslint .` / `eslint . --fix` commands. Also use whenever you see `@nuxt/eslint` in `package.json` or an `eslint.config.mjs` that imports `withNuxt`, even if the user doesn't explicitly mention it."
---

# @nuxt/eslint

The official Nuxt module for ESLint. Generates a project-aware **flat config** for Nuxt projects, bundles the `eslint-plugin-vue`, `typescript-eslint`, and `@nuxt/eslint-plugin` rule sets, and (optionally) integrates an ESLint checker into the dev server and surfaces the Config Inspector in Nuxt DevTools.

Current major version: **v1.x** (targets Nuxt 3 and 4, ESLint 8.45+ / 9).

## When to use this skill

- Adding ESLint to a Nuxt 3/4 project (fresh install)
- Editing `eslint.config.mjs` — the Nuxt flat config entry point
- Tuning rules via `withNuxt()` / `createConfigForNuxt()` / `.override()` / `.prepend()`
- Toggling `config.stylistic`, `config.typescript`, `config.standalone`, `config.checker`, `config.autoInit`
- Pairing Nuxt ESLint with Prettier (the recommended formatting path)
- Migrating from the deprecated `@nuxtjs/eslint-module` or a legacy `.eslintrc` config
- Reading/writing `eslint .` / `eslint . --fix` output in a Nuxt codebase

## Mental model: three packages, one module

The `@nuxt/eslint` ecosystem is three npm packages — usually you install only the first:

| Package | What it is | When to use |
|---|---|---|
| `@nuxt/eslint` | Nuxt module. Registers in `modules`, generates `eslint.config.mjs`, surfaces DevTools inspector, optional dev-server checker. | Default choice for any Nuxt project. |
| `@nuxt/eslint-config` | Standalone flat-config factory (`createConfigForNuxt(...)`). No module, no DevTools. | You want the Nuxt preset in a non-Nuxt project or in a custom flat config you fully own. |
| `@nuxt/eslint-plugin` | Low-level plugin with Nuxt-specific rules only (used internally). | You're assembling a custom ESLint setup and just want the Nuxt-specific rules. |

Under the hood, the module calls `createConfigForNuxt()` from `eslint-config` and adds project-aware knowledge from `nuxt.config.ts` (auto-imports, layers, components, composables — so `no-undef` doesn't fire on `useRoute()`, `<MyComponent />`, etc.).

Key conventions:
- **Flat config only.** Legacy `.eslintrc*` is not supported. ESLint 8.45+ supports flat config; ESLint 9+ makes it the default.
- The generated `eslint.config.mjs` imports from `./.nuxt/eslint.config.mjs` — that file is produced by `nuxt prepare` (or dev server startup) based on your `nuxt.config.ts`. So `eslint.config.mjs` is composition-only; the Nuxt half is regenerated.
- `withNuxt()` returns a chainable `FlatConfigComposer` (from `eslint-flat-config-utils`) — it's a Promise AND has `.prepend()`, `.override()`, etc.

## Installation

### Blessed path (what you'll usually want)

```shell
npx nuxt module add eslint
```

This single command:
1. Installs `@nuxt/eslint` (and pulls in `eslint` / `typescript` as peer deps that you need to install separately if missing).
2. Registers the module in `nuxt.config.ts`.
3. Generates a minimal `eslint.config.mjs` at project root on next `nuxt prepare`.

**Post-install checks:**
- `@nuxt/eslint` is added to `dependencies` by default — move it to `devDependencies` manually if you prefer (it's a dev-only tool).
- Install `eslint` and `typescript` explicitly if they're not already there: `pnpm add -D eslint typescript`.
- Run `nuxt prepare` (or let postinstall do it) so `.nuxt/eslint.config.mjs` exists.

### Manual install

```shell
pnpm add -D @nuxt/eslint eslint typescript
```

Add to `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
  eslint: {
    // options — see below
  }
})
```

Create `eslint.config.mjs`:

```js
// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  // Your custom flat-config entries append after Nuxt's
)
```

### `package.json` scripts

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:ci": "eslint . --max-warnings=0 --report-unused-disable-directives"
  }
}
```

Why `--max-warnings=0` in CI: ESLint exits 0 on warnings by default. CI should fail on warnings too if you want clean diffs. `--report-unused-disable-directives` catches stale `eslint-disable` comments.

## Module options (`nuxt.config.ts` → `eslint: { ... }`)

Full shape:

```ts
export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
  eslint: {
    config: {
      // Stylistic/formatting rules from @stylistic/eslint-plugin.
      // Default: false. Keep false when using Prettier.
      stylistic: false,
      // Or enable + customize:
      // stylistic: { indent: 'tab', semi: true, quotes: 'single' },

      // TypeScript support (non-type-aware rules by default).
      typescript: true,
      // Type-aware (slow) — requires a tsconfig path:
      // typescript: { tsconfigPath: './tsconfig.json' },

      // Whether the module installs JS/TS/Vue preset rules.
      // Set to false if you're combining with another preset like @antfu/eslint-config.
      standalone: true,

      // Auto-generate eslint.config.mjs on server start if missing.
      autoInit: true,

      // Project root for layer detection; rarely overridden.
      // rootDir: '/abs/path',
    },

    // Opt-in dev-server ESLint checker.
    checker: false,
    // Or: checker: true
    // Or: checker: { configType: 'flat', fix: false, ... }
  }
})
```

Notes:
- **`config.stylistic: false` is the default.** Paired with Prettier, nothing more is needed — no `eslint-config-prettier`.
- **`config.standalone: false`** is for users combining Nuxt rules with `@antfu/eslint-config` or similar. When false, only Nuxt-specific rules come through; your external preset provides JS/TS/Vue.
- **`checker: true`** runs ESLint in the dev server via `vite-plugin-eslint2`. You need to install that separately (`pnpm add -D vite-plugin-eslint2`). Typically unnecessary if team uses editor-integrated ESLint + pre-commit hooks.

## `eslint.config.mjs` patterns

`withNuxt()` takes additional flat-config entries as varargs and returns a chainable composer.

### Add a custom flat config entry

```js
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  {
    files: ['**/*.ts', '**/*.tsx'],
    rules: {
      'no-console': 'off',
    },
  }
)
```

### Override a rule inside a specific Nuxt-provided config

```js
export default withNuxt()
  .override('nuxt/typescript/rules', {
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  })
  .override('nuxt/vue/rules', {
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  })
```

Config names to target come from the live config — inspect via Nuxt DevTools' Config Inspector or `npx @eslint/config-inspector`. Common ones: `nuxt/base/rules`, `nuxt/typescript/rules`, `nuxt/vue/rules`, `nuxt/stylistic/rules` (if stylistic is on), `nuxt/import/rules`.

### Prepend a config (runs before Nuxt's)

```js
export default withNuxt()
  .prepend(
    // e.g. ignores that should apply to Nuxt's rules too
    { ignores: ['**/__generated__/**', '**/*.generated.ts'] }
  )
```

### Use `@antfu/eslint-config` alongside Nuxt rules

```js
import antfu from '@antfu/eslint-config'
import withNuxt from './.nuxt/eslint.config.mjs'

// In nuxt.config.ts set: eslint: { config: { standalone: false } }

export default withNuxt(
  antfu({
    // @antfu/eslint-config options
  })
)
```

### Standalone (no module)

```js
// eslint.config.mjs
import { createConfigForNuxt } from '@nuxt/eslint-config'

export default createConfigForNuxt({
  features: {
    stylistic: false,       // keep false for Prettier
    typescript: true,
    tooling: false,         // unicorn/regexp/jsdoc rules for module authors
  },
})
```

Note the name change: the **module** uses `config.stylistic` (flattened); the **standalone factory** uses `features.stylistic` (nested under `features`). Same flag, two nesting shapes. See `references/configuration.md` for details.

## CLI

```shell
eslint .                                      # lint everything
eslint . --fix                                # apply safe auto-fixes
eslint path/to/file.ts                        # lint a specific file or glob (shell-expanded)
eslint . --cache                              # cache results; faster reruns
eslint . --max-warnings=0                     # fail on warnings (CI)
eslint . --report-unused-disable-directives   # flag stale // eslint-disable-* comments
eslint . --no-warn-ignored                    # suppress "file ignored because of .eslintignore" warnings
eslint . --rule "no-console: error"           # ad-hoc rule for one run
```

Exit codes: `0` clean, `1` diagnostics, `2` config / CLI error.

See `references/cli.md` for every CLI flag and common workflow recipes.

## Integrating with Prettier

The recommended modern setup:

1. Install Prettier pinned: `pnpm add -D -E prettier`.
2. Create `.prettierrc.json` + `.prettierignore`.
3. Keep `config.stylistic: false` in `nuxt.config.ts` (the default).
4. Run them separately — ESLint for code quality, Prettier for formatting.

You do **not** need `eslint-config-prettier` when `config.stylistic: false`, because `@nuxt/eslint` doesn't enable the conflicting formatting rules in the first place. If you're combining with `@antfu/eslint-config` or another preset that does enable stylistic rules, `eslint-config-prettier` becomes relevant again — append it as the last entry to strip conflicts.

`package.json` scripts:

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier . --write",
    "format:check": "prettier . --check"
  }
}
```

For deeper Prettier setup, see the `prettier` skill.

## Vue + auto-imports

`@nuxt/eslint` pre-wires `eslint-plugin-vue` recommended rules and teaches ESLint about Nuxt's auto-imports, so the following don't false-positive:

- Components auto-imported from `~/components`
- Composables from `~/composables`
- Utils from `~/utils`
- Global Nuxt composables: `useRoute`, `useRouter`, `useFetch`, `navigateTo`, `defineNuxtPlugin`, etc.
- Vue compiler macros: `defineProps`, `defineEmits`, `defineExpose`, `withDefaults`

If you see `no-undef` on something Nuxt auto-imports, run `nuxt prepare` — `.nuxt/eslint.config.mjs` is regenerated from the current Nuxt state, and your new composables / components only show up after a prepare.

Notable bundled Vue rules (all from `eslint-plugin-vue`):
- `vue/multi-word-component-names` — often turned off for pages in Nuxt (`index.vue`, `error.vue`, etc.).
- `vue/no-unused-vars`, `vue/no-unused-components`
- `vue/require-default-prop`, `vue/require-prop-types`
- `vue/attribute-hyphenation`, `vue/v-on-event-hyphenation`

## TypeScript

Default TS setup uses `typescript-eslint`'s **non-type-aware** rules (fast). Opt into **type-aware** rules by pointing at a `tsconfig.json`:

```ts
eslint: {
  config: {
    typescript: { tsconfigPath: './tsconfig.json' }
  }
}
```

Type-aware rules unlock things like `@typescript-eslint/no-floating-promises`, `no-misused-promises`, `no-unnecessary-condition`. Cost: ESLint builds a TypeScript program before each lint, which can be 5-10x slower on larger repos. Common pattern: type-aware rules in CI only.

## Dev server checker (optional)

```ts
eslint: { checker: true }
```

Plus: `pnpm add -D vite-plugin-eslint2`. Then ESLint runs on every file change during `nuxt dev` and surfaces issues in the terminal / browser overlay. Disabled by default because most devs rely on editor integration + pre-commit hooks, and the checker noticeably slows the dev server.

## Common gotchas

- **`eslint.config.mjs` imports from `./.nuxt/...`.** Without a `nuxt prepare` run, that file won't exist and `eslint .` will fail to resolve the import. `postinstall: "nuxt prepare"` in `package.json` handles this automatically.
- **`@nuxt/eslint` installs as a `dependency`** via `nuxt module add`. Move it to `devDependencies` manually — it's not needed at runtime.
- **`eslint` and `typescript` are peer deps.** `nuxt module add eslint` doesn't always install them for you. Run `pnpm add -D eslint typescript` if they're missing.
- **Legacy `.eslintrc*` not supported.** If you're migrating, delete the old config and run `nuxt module add eslint` to generate a fresh flat config; port any custom rules into `eslint.config.mjs`.
- **VS Code ESLint extension < v3.0.10** needs `"eslint.useFlatConfig": true` in `.vscode/settings.json`. v3.0.10+ auto-detects.
- **`config.stylistic` vs `features.stylistic`.** The Nuxt *module* uses `eslint.config.stylistic` (flattened). The `@nuxt/eslint-config` *standalone factory* uses `features.stylistic` (nested). Same thing, two surfaces.
- **Pairing with Prettier:** keep `config.stylistic: false`. Adding `eslint-config-prettier` on top is harmless but redundant in this setup.
- **`@nuxtjs/eslint-module` (old community module) is not the same package.** Migrate by replacing the module entry with `'@nuxt/eslint'` and regenerating config.

## Reference index

- `references/configuration.md` — full module option reference, composer API (`withNuxt` / `createConfigForNuxt`), config names to target with `.override()`
- `references/cli.md` — every ESLint CLI flag relevant in Nuxt projects, caching, output formats
- `references/rules.md` — bundled rule sets (eslint-plugin-vue, typescript-eslint, @nuxt/eslint-plugin), common tuning recipes, severity conventions
- `references/integrations.md` — Prettier pairing, editor setup, git hooks, CI, DevTools Config Inspector
- `references/migration.md` — migrating from `@nuxtjs/eslint-module` and legacy `.eslintrc*`
