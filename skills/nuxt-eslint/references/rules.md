# Bundled rule sets and common tuning

`@nuxt/eslint` (with `config.standalone: true`, the default) activates rule sets from three plugins. This file maps what's on, what commonly trips, and how to tune.

## Rule plugins bundled

| Plugin | Provides | Default severity |
|---|---|---|
| `eslint-plugin-vue` | Vue SFC rules — template, `<script setup>`, naming, directive usage | Varies by rule; most at `warn` |
| `typescript-eslint` | TS-specific rules — types, any, unused, naming | Varies (warn/error) |
| `@nuxt/eslint-plugin` | Nuxt-specific — e.g. `nuxt/prefer-import-meta` | `warn` / `error` |
| `@stylistic/eslint-plugin` | Formatting rules (only when `config.stylistic` is true) | `error` |

Plus core ESLint rules that `typescript-eslint` doesn't re-provide: `no-console`, `no-debugger`, `no-empty`, etc.

## Rule severity conventions

| Severity | Use in output | When to use |
|---|---|---|
| `"off"` / `0` | — | Rule disabled |
| `"warn"` / `1` | Yellow; doesn't fail `eslint .` by default | Style preferences, nice-to-have cleanups |
| `"error"` / `2` | Red; exit code 1 | Real bugs, must-fix |

In CI you typically want `--max-warnings=0` so warnings fail builds too.

## Noteworthy Vue rules (from `eslint-plugin-vue`)

| Rule | Default | When to tune |
|---|---|---|
| `vue/multi-word-component-names` | error | Off for Nuxt pages/layouts/error.vue — they're always single-word by Nuxt convention. |
| `vue/no-unused-vars` | warn | Rarely tuned. |
| `vue/no-unused-components` | warn | Rarely tuned. |
| `vue/require-default-prop` | warn | Off if you use TS-only props (defaults come from destructuring). |
| `vue/require-prop-types` | warn | Off if using `defineProps<Props>()`. |
| `vue/attribute-hyphenation` | warn | Sometimes off for custom elements. |
| `vue/v-on-event-hyphenation` | warn | Same. |
| `vue/html-self-closing` | — | Mostly relevant when `config.stylistic` is on. |
| `vue/component-api-style` | — | Worth enabling as `["error", ["script-setup"]]` to enforce `<script setup>`. |

Common override:

```js
export default withNuxt(
  {
    files: ['**/pages/**/*.vue', '**/layouts/**/*.vue', '**/error.vue'],
    rules: {
      'vue/multi-word-component-names': 'off'
    }
  }
)
```

The module already ships something like this; check `npx @eslint/config-inspector` to see whether it covers your cases.

## Noteworthy TypeScript rules (from `typescript-eslint`)

| Rule | Default | Notes |
|---|---|---|
| `@typescript-eslint/no-explicit-any` | warn | Very common to keep at `warn` or `off` on legacy code. |
| `@typescript-eslint/no-unused-vars` | error | Configure `argsIgnorePattern: '^_'` + `varsIgnorePattern: '^_'` to allow `_unused` names. |
| `@typescript-eslint/no-empty-interface` | warn | Off if using interface-for-name-only patterns. |
| `@typescript-eslint/no-non-null-assertion` | warn | Sometimes off when you deliberately use `!`. |
| `@typescript-eslint/ban-ts-comment` | error | Tune severity of specific directives: `ts-ignore: error, ts-expect-error: warn, ts-nocheck: off`. |
| `@typescript-eslint/consistent-type-imports` | warn | Prefer `import type { ... }`. Auto-fixable. |

Type-aware rules (need `config.typescript.tsconfigPath`):
- `@typescript-eslint/no-floating-promises` — every async expression must be awaited or `.catch()`'d.
- `@typescript-eslint/no-misused-promises` — no passing a promise where a sync function is expected.
- `@typescript-eslint/no-unnecessary-condition` — flag `if (x)` where `x` is always truthy/falsy by type.
- `@typescript-eslint/no-unsafe-assignment`, `no-unsafe-call`, `no-unsafe-argument` — catch `any` leaks.

These are great-but-slow. Common pattern: enable in CI only, skip locally.

## Noteworthy Nuxt rules (from `@nuxt/eslint-plugin`)

| Rule | Purpose |
|---|---|
| `nuxt/prefer-import-meta` | Prefer `import.meta.server` / `import.meta.client` over deprecated `process.server` / `process.client`. |
| `nuxt/nuxt-config-keys-order` | Enforces a canonical key order in `nuxt.config.ts`. |
| `nuxt/no-cjs-in-config` | Disallow `require()` in `nuxt.config.ts` (should be ESM). |

## Common tuning recipes

### Adopting ESLint on a legacy codebase — quiet the top offenders

```js
export default withNuxt()
  .override('nuxt/typescript/rules', {
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
      }],
    }
  })
```

Tighten gradually as you fix the backlog.

### Tests allow `any`, unused vars, long lines

```js
export default withNuxt(
  {
    files: ['**/*.test.ts', '**/*.spec.ts', '**/__tests__/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
    }
  }
)
```

### Server / API routes need default exports

Nuxt's event handlers are usually default-exported. The module already disables `no-default-export` in `server/api/**` and `server/routes/**`, but if you add custom server dirs, extend:

```js
export default withNuxt(
  {
    files: ['server/middleware/**/*.ts', 'server/plugins/**/*.ts'],
    rules: { 'import/no-default-export': 'off' }
  }
)
```

### Enforce `<script setup>` composition API

```js
export default withNuxt(
  {
    files: ['**/*.vue'],
    rules: {
      'vue/component-api-style': ['error', ['script-setup']]
    }
  }
)
```

### Allow `console.log` in scripts only

```js
export default withNuxt(
  {
    files: ['scripts/**/*.ts', 'scripts/**/*.mjs'],
    rules: { 'no-console': 'off' }
  }
)
```

## Suppression syntax

```ts
// Single line
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const foo: any = external()

// Inline
const bar: any = external() // eslint-disable-line @typescript-eslint/no-explicit-any

// Block
/* eslint-disable @typescript-eslint/no-explicit-any */
// ... many lines ...
/* eslint-enable @typescript-eslint/no-explicit-any */

// File-wide (at top of file)
/* eslint-disable @typescript-eslint/no-explicit-any */
```

Multi-rule: `eslint-disable-next-line rule-a, rule-b`.

ESLint does NOT require a reason comment (unlike Biome's `biome-ignore`). Convention: still add a reason inline.

Stale suppressions — use `--report-unused-disable-directives` in CI to flag disables that no longer match any diagnostic.

## Inspecting the live config

The Config Inspector is the authoritative answer to "what rule is on, and who enabled it?":

```shell
npx @eslint/config-inspector
```

Opens a browser UI. Select a file path to see every rule that applies, from which config entry, with severity and options. Useful for:
- Finding the name of a Nuxt-provided config to `.override()` against.
- Confirming a rule is actually on before trying to disable it.
- Debugging why an override isn't taking effect (another config entry may be re-enabling it).

The same inspector is available in Nuxt DevTools (ESLint tab).
