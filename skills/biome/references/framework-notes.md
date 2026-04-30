# Framework-specific notes

Caveats, config snippets, and gotchas per framework. Support levels change — always defer to the version of Biome installed in the project.

## Language support status (v2.4)

| Language | Parse | Format | Lint | Notes |
|---|---|---|---|---|
| JavaScript / TypeScript | ✅ | ✅ | ✅ | ES2024 / TS 5.9 |
| JSX / TSX | ✅ | ✅ | ✅ | `javascript.jsxRuntime: "automatic"` is default |
| JSON / JSONC | ✅ | ✅ | ✅ | well-known files auto-detected |
| CSS | ✅ | ✅ | ✅ | Tailwind v4 directives via `css.parser.tailwindDirectives: true` |
| GraphQL | ✅ | ✅ | ✅ | |
| HTML | ✅ | ✅ | ✅ | opt-in: `html.experimentalFullSupportEnabled: true` |
| Vue | 🟡 | 🟡 | 🟡 | experimental; v2.3+ |
| Svelte | 🟡 | 🟡 | 🟡 | experimental; v2.3+ |
| Astro | 🟡 | 🟡 | 🟡 | experimental; v2.3+ |
| SCSS | ⌛ | ⌛ | 🚫 | parser in progress |
| YAML | ⌛ | ⌛ | 🚫 | parser in progress |
| Markdown | ⌛ | ⌛ | 🚫 | parser in progress |

## Vue

Biome formats and lints the `<script>`, `<style>`, and (partially) `<template>` sections of `.vue` files. Vue-specific template directives (`v-if`, `v-for`, etc.) and custom control-flow are **not** understood yet — formatting can produce unexpected results inside templates, and lint rules that reason about identifier usage can false-positive when identifiers are referenced only in templates.

Recommended override to silence the common false positives:

```jsonc
{
  "overrides": [
    {
      "includes": ["**/*.vue"],
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

The `vue` linter domain (auto-enables with `vue ≥ 3` in `package.json`) adds Vue-specific rules. You can configure it:

```jsonc
{ "linter": { "domains": { "vue": "recommended" } } }
```

**Nuxt** specifics: nothing Nuxt-aware baked in beyond Vue. Exclude build output explicitly:

```jsonc
{
  "files": {
    "includes": ["**", "!!**/.nuxt", "!!**/.output", "!!**/.data", "!!**/.nitro", "!!**/.cache"]
  }
}
```

Nuxt auto-imports can make `noUnusedImports` and `useImportType` noisy in `.vue` files — the override above handles that.

## Svelte / Astro

Same caveats as Vue. Use the same override pattern, extended to the respective file extensions:

```jsonc
{
  "overrides": [
    {
      "includes": ["**/*.svelte", "**/*.astro"],
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

Svelte `{#if}` / `{#each}` blocks and Astro's fenced frontmatter aren't specially parsed — formatting and linting the template bodies of these files is best-effort.

## React

The `react` domain auto-enables when `react ≥ 16` is in `package.json`. It adds:

- Hook rules: `useExhaustiveDependencies`, `useHookAtTopLevel`.
- JSX rules: `useJsxKeyInIterable`, `noChildrenProp`, `noArrayIndexKey`.
- Performance: `noNestedComponentDefinitions`, `noRenderReturnValue`.
- Framework safety: `noDuplicateJsxProps`, `noVoidElementsWithChildren`.

JSX-specific formatter options are under `javascript.formatter`:

```jsonc
{
  "javascript": {
    "formatter": {
      "jsxQuoteStyle": "double",
      "bracketSameLine": false
    },
    "jsxRuntime": "automatic"   // removes need for `import React`
  }
}
```

## Next.js

The `next` domain auto-enables with `next ≥ 14`. Extends `react` and adds Next-specific rules for `next/image`, `next/script`, `next/head`, async server components, and `app/` router conventions.

```jsonc
{ "linter": { "domains": { "next": "recommended" } } }
```

Exclude Next's build output:

```jsonc
{ "files": { "includes": ["**", "!!**/.next", "!!**/out"] } }
```

## React Native

The `react-native` domain auto-enables with `react-native ≥ 0.60`. Adds RN-specific platform-API and style-object rules.

## Solid / Qwik

`solid` and `qwik` domains auto-enable when their packages are detected. Solid's domain focuses on destructured props (they break reactivity); Qwik's on serialization and `$` suffix conventions.

## Tailwind CSS

### Directive parsing (Tailwind v4)

Tailwind v4 moves config into CSS (`@theme`, `@apply`, `@utility`, `@variant`, `@source`, `@import "tailwindcss"`). By default Biome's CSS parser warns on these unknown at-rules. Turn parsing on:

```jsonc
{
  "css": {
    "parser": { "tailwindDirectives": true }
  }
}
```

### Class sorting

`lint/nursery/useSortedClasses` implements the same sort order as `prettier-plugin-tailwindcss`. It's in the `nursery` group (experimental) and its fix is **unsafe**.

Turning it on:

```jsonc
{
  "linter": {
    "rules": {
      "nursery": {
        "useSortedClasses": {
          "level": "warn",
          "options": {
            "functions": ["clsx", "cva", "cn", "tw", "twMerge"]
          }
        }
      }
    }
  }
}
```

Known limitations:
- Only default Tailwind config is recognized. Custom utilities/variants defined via plugins are **not** sorted correctly.
- Screen-variant ordering (`md:`, `max-lg:`) isn't handled.
- Because the rule is a lint rule (not a formatter), editor "format on save" will **not** sort — you need `biome check --write --unsafe` or an explicit editor code action on save.

Tracking issue: https://github.com/biomejs/biome/issues/1274.

## Testing frameworks

The `test` domain auto-enables when `jest`, `vitest`, `mocha`, or `ava` is in `package.json`. Adds:
- `noFocusedTests` (forbids `.only`)
- `noDisabledTests` (forbids `.skip`)
- `noDuplicateTestHooks`
- Various correctness rules for common test shapes

Tests often need looser type/style rules — use an override:

```jsonc
{
  "overrides": [
    {
      "includes": ["**/*.test.ts", "**/*.spec.ts", "**/__tests__/**"],
      "linter": {
        "rules": {
          "suspicious": { "noExplicitAny": "off" },
          "style": { "useNamingConvention": "off" }
        }
      }
    }
  ]
}
```

## Drizzle

The `drizzle` domain auto-enables with `drizzle-orm ≥ 0.9`. Adds ORM-specific correctness checks. Nothing to configure manually beyond the domain toggle.

## Playwright

The `playwright` domain auto-enables with `@playwright/test ≥ 1`. Adds Playwright-specific test rules.

## Turborepo

The `turborepo` domain auto-enables with `turbo ≥ 1`. Adds pipeline-config correctness checks.

## Monorepo structure tips

- Keep one root `biome.jsonc` with the common settings (formatter style, base rule severities, global `files.includes`).
- In each package, add a small `biome.jsonc` with `"extends": "//"` and `"root": false`. Override only what's truly different per package.
- Exclude tooling/build output at the root with `!!` globs so the scanner skips them in every package.

## Framework-specific file extensions Biome handles

`.js`, `.cjs`, `.mjs`, `.jsx`, `.ts`, `.cts`, `.mts`, `.tsx`, `.d.ts`, `.json`, `.jsonc`, `.css`, `.gql`, `.graphql`, `.html`, `.vue`, `.svelte`, `.astro`.

File extensions **not** yet supported: `.scss`, `.sass`, `.less`, `.yaml`, `.yml`, `.md`, `.mdx`.
