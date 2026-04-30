# @nuxt/eslint configuration reference

Complete reference for the module options, the `@nuxt/eslint-config` standalone factory, and the `FlatConfigComposer` API exposed by `withNuxt()`.

## Module options (`nuxt.config.ts` → `eslint: { ... }`)

```ts
export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
  eslint: {
    // All config options are under `config`.
    config: {
      stylistic: false,        // boolean | StylisticCustomizeOptions
      typescript: true,        // boolean | { tsconfigPath?: string }
      standalone: true,        // whether to install JS/TS/Vue presets (false when combining with @antfu etc.)
      autoInit: true,          // auto-create eslint.config.mjs on dev server start if missing
      // rootDir: '/abs/path', // rarely overridden
    },

    // Dev-server ESLint checker (opt-in).
    checker: false,            // boolean | CheckerOptions

    // Other less-used options:
    // lintOnStart: false,
    // cache: true,
  }
})
```

### `config.stylistic`

- `false` (default) — no formatting rules enabled. Pair with Prettier.
- `true` — enable ESLint Stylistic's recommended formatting rules.
- Object — customize: `{ indent: 'tab' | number, semi: boolean, quotes: 'single' | 'double', ... }`. Full option list at https://eslint.style.

Example:

```ts
eslint: {
  config: {
    stylistic: { indent: 2, semi: false, quotes: 'single' }
  }
}
```

### `config.typescript`

- `true` (default) — enable typescript-eslint's **non-type-aware** recommended rules.
- `{ tsconfigPath: './tsconfig.json' }` — enable type-aware rules (slow; runs TS program).
- `false` — disable TS rules entirely.

### `config.standalone`

- `true` (default) — the module installs JS, TS, and Vue presets.
- `false` — skip presets; only Nuxt-specific rules come through. Use when combining with another preset like `@antfu/eslint-config` that brings its own JS/TS/Vue rules.

### `config.autoInit`

- `true` (default) — generate `eslint.config.mjs` at project root if missing, on `nuxt dev` or `nuxt prepare`.
- `false` — don't auto-generate; you own the file entirely.

### `config.nuxt`

Project-aware options. Typically omitted and derived from `nuxt.config.ts`.

### `checker`

Opt-in dev-server ESLint integration. Needs a peer plugin:

- Vite (default): `pnpm add -D vite-plugin-eslint2`
- Webpack: `pnpm add -D eslint-webpack-plugin`

```ts
eslint: {
  checker: true
  // or: checker: { configType: 'flat', fix: false, emitWarning: true, emitError: true }
}
```

Set `configType: 'eslintrc'` only if you're still on legacy config (not recommended).

## Standalone factory: `createConfigForNuxt()` (`@nuxt/eslint-config`)

When using `@nuxt/eslint-config` **without** the module:

```js
// eslint.config.mjs
import { createConfigForNuxt } from '@nuxt/eslint-config'

export default createConfigForNuxt({
  features: {
    stylistic: false,                          // boolean | StylisticCustomizeOptions
    typescript: true,                          // boolean | { tsconfigPath: './tsconfig.json' }
    tooling: false,                            // boolean | { unicorn, regexp, jsdoc } — for module authors
  },
  // dirs?: {...}                              // project dir overrides
})
  .prepend(/* configs before Nuxt's */)
  .append(/* configs after */)
  .override('nuxt/typescript/rules', { rules: { /* ... */ } })
```

**Note the surface difference:**
- Module: options under `eslint.config.stylistic` (flattened)
- Standalone factory: options under `features.stylistic` (nested)

The module wraps `createConfigForNuxt()` and flattens `features` into `config`.

### `features.tooling`

For module/library authors. Enables stricter rules via the `unicorn`, `regexp`, and `jsdoc` plugins. Experimental.

```js
createConfigForNuxt({
  features: {
    tooling: true
    // or: tooling: { unicorn: true, regexp: false, jsdoc: true }
  }
})
```

## `FlatConfigComposer` API

`withNuxt()` and `createConfigForNuxt()` both return a `FlatConfigComposer` from `eslint-flat-config-utils`. It's chainable AND a Promise (ESLint awaits it).

### Adding configs

```js
export default withNuxt(
  // These entries APPEND after Nuxt's configs (varargs).
  { files: ['**/*.ts'], rules: { 'no-console': 'off' } },
  myOtherConfig,
)
```

Or via methods:

```js
export default withNuxt()
  .append({ rules: { 'no-console': 'off' } })
  .prepend({ ignores: ['**/__generated__/**'] })
```

### Overriding rules in a specific config

```js
export default withNuxt()
  .override('nuxt/typescript/rules', {
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn'
    }
  })
```

Config names come from Nuxt's internal composition. Common ones:
- `nuxt/base/rules` — core ESLint rules
- `nuxt/typescript/rules` — typescript-eslint rules
- `nuxt/vue/rules` — eslint-plugin-vue rules
- `nuxt/vue/notype` — Vue rules that don't need type info
- `nuxt/import/rules` — import-related rules
- `nuxt/stylistic/rules` — only exists when `config.stylistic` is truthy
- `nuxt/disables/routes` — auto-disables for `server/api/**` (e.g. `no-default-export`)
- `nuxt/disables/scripts` — disables for `scripts/**`
- `nuxt/tooling/regexp`, `nuxt/tooling/unicorn`, `nuxt/tooling/jsdoc` — only with `features.tooling`

**To discover names in YOUR project:** open Nuxt DevTools → Config Inspector, or run:

```shell
npx @eslint/config-inspector
```

It opens a browser UI listing every config entry with its name, files, rules, and source.

### Renaming / removing configs

```js
export default withNuxt()
  .remove('nuxt/disables/routes')       // drop a Nuxt-provided config
  .renamePlugins({ 'vue': 'my-vue' })   // uncommon
```

### `.insertAfter(name, config)` / `.insertBefore(name, config)`

Insert a config at a specific position relative to another by name:

```js
export default withNuxt()
  .insertAfter('nuxt/vue/rules', {
    files: ['**/*.vue'],
    rules: { 'vue/multi-word-component-names': 'off' }
  })
```

### Using as a Promise

```js
const resolved = await withNuxt()
// Array of resolved flat-config entries
```

Useful for inspection or for passing to tools that expect a resolved array.

## Generated `eslint.config.mjs` anatomy

```js
// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  // your custom flat configs here
)
```

`./.nuxt/eslint.config.mjs` is written by `nuxt prepare`. It exports `withNuxt` which, when called, returns a composer already populated with:

1. Ignores: `.nuxt`, `.output`, `node_modules`, `dist`, etc.
2. Global setup: `languageOptions.globals` for Nuxt auto-imports, compiler macros, browser globals.
3. Per-language parsers: `@typescript-eslint/parser` for TS, `vue-eslint-parser` for Vue.
4. Rule entries (if `config.standalone` is true): JS, TS, Vue, import-related rules with sensible defaults.
5. Directory-specific disables (e.g., `no-default-export: 'off'` for `server/api/**`, `pages/**`, `layouts/**`).

## Common config recipes

### Turn off rules for a specific path

```js
export default withNuxt(
  {
    files: ['server/**/*.ts'],
    rules: {
      // Nuxt allows default exports here; we might also allow console.
      'no-console': 'off'
    }
  }
)
```

### Relaxed rules in tests

```js
export default withNuxt(
  {
    files: ['**/*.test.ts', '**/*.spec.ts', '**/__tests__/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off'
    }
  }
)
```

### Global ignores beyond Nuxt defaults

```js
export default withNuxt()
  .prepend({ ignores: ['**/__generated__/**', '**/*.generated.*'] })
```

### Combine with `@antfu/eslint-config`

```ts
// nuxt.config.ts
eslint: { config: { standalone: false } }
```

```js
// eslint.config.mjs
import antfu from '@antfu/eslint-config'
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  antfu({ vue: true, typescript: true })
)
```

### Enable type-aware rules (CI only)

Keep the default non-type-aware config for dev speed. In CI:

```shell
TSCONFIG_PATH=./tsconfig.json eslint . --max-warnings=0
```

And in `eslint.config.mjs`:

```js
export default withNuxt(
  process.env.TSCONFIG_PATH ? {
    languageOptions: {
      parserOptions: { project: process.env.TSCONFIG_PATH }
    }
  } : {}
)
```

Alternatively, set `eslint.config.typescript = { tsconfigPath: './tsconfig.json' }` always and accept the slower dev loop.
