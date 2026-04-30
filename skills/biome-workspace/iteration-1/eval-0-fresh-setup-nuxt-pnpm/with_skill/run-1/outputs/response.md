Here's a Biome setup tuned for your Nuxt 4 + Tailwind v4 project.

## `biome.jsonc`

Drop this at the repo root.

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",

  // Respect .gitignore so Biome skips untracked build artifacts automatically,
  // and enable --staged / --changed for fast hook + PR-scoped runs.
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  },

  "files": {
    // Skip anything Biome doesn't recognize (e.g. .md, .yaml) instead of erroring.
    "ignoreUnknown": true,
    // `!!` (double-bang) also excludes these paths from Biome's project scanner,
    // which matters for performance on a Nuxt project with large generated dirs.
    "includes": [
      "**",
      "!!**/node_modules",
      "!!**/.nuxt",
      "!!**/.output",
      "!!**/.data",
      "!!**/.nitro",
      "!!**/.cache",
      "!!**/dist",
      "!pnpm-lock.yaml"
    ]
  },

  "formatter": {
    "enabled": true,
    // Biome defaults to tabs — switch to 2-space to match the existing codebase.
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100,
    "lineEnding": "lf"
  },

  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
    // The `vue` domain auto-enables when vue >= 3 is in package.json — no need
    // to list it explicitly. Avoid the `project`/`types` domains; they build a
    // module graph and slow every run down significantly.
  },

  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "jsxQuoteStyle": "double",
      "semicolons": "asNeeded",
      "trailingCommas": "all",
      "arrowParentheses": "always",
      "bracketSpacing": true,
      "bracketSameLine": false
    }
  },

  "json": {
    "formatter": {
      "trailingCommas": "none"
    }
  },

  // Tailwind v4 puts config in CSS (@theme, @apply, @utility, @variant, @source).
  // Without this flag Biome's CSS parser warns on those as unknown at-rules.
  "css": {
    "parser": {
      "tailwindDirectives": true
    },
    "formatter": {
      "quoteStyle": "double"
    }
  },

  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  },

  "overrides": [
    {
      // biome.jsonc (and friends) should stay comment/trailing-comma friendly.
      "includes": ["**/*.jsonc"],
      "json": {
        "parser": { "allowComments": true, "allowTrailingCommas": true },
        "formatter": { "trailingCommas": "none" }
      }
    },
    {
      // Vue support is experimental. Identifiers referenced only in <template>
      // look "unused" to Biome, and Nuxt auto-imports exacerbate this. Also
      // soften a couple of style rules that over-trigger inside <script setup>.
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

Notable choices mapped to what you asked for:

- `indentStyle: "space"` + `indentWidth: 2` — Biome defaults to tabs, so this is required.
- `lineWidth: 100` — matches your target.
- `quoteStyle: "single"`, `semicolons: "asNeeded"`, `trailingCommas: "all"` — your stated style.
- `css.parser.tailwindDirectives: true` — lets Biome parse `@theme`, `@apply`, `@utility`, `@variant`, `@source`, `@import "tailwindcss"` without warnings.
- `files.includes` excludes all the Nuxt/Nitro generated dirs (`.nuxt`, `.output`, `.data`, `.nitro`, `.cache`) with double-bang so they're skipped by the project scanner, not just by lint/format.
- `vcs.useIgnoreFile: true` — Biome will layer `.gitignore` on top of the includes automatically.

## `package.json` scripts

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

Day to day you'll mostly want `pnpm check:fix`. `pnpm ci` is the read-only variant you wire into CI — it emits GitHub annotations automatically, rejects `--write`, and supports `--changed` for PR-scoped runs.

## Vue caveat — worth knowing before you run it

Biome's Vue support is **experimental** (stable as of v2.3, but still flagged as such). Concretely:

- **`<template>` is only partially understood.** Vue-specific directives (`v-if`, `v-for`, slot syntax, custom control flow) aren't fully parsed. `<script>` and `<style>` blocks format and lint normally; the template body is best-effort.
- **Identifiers used only in `<template>` look unused.** Biome's linter can't always see template usage of a `ref`/`computed`/imported component, so `noUnusedVariables` / `noUnusedImports` will false-positive. The `**/*.vue` override in the config above disables those four rules inside `.vue` files — the same recipe Biome's own docs recommend.
- **Nuxt auto-imports amplify this.** Things like `useFetch`, `useState`, `useRoute`, `definePageMeta`, `defineNuxtConfig`, etc. aren't explicitly imported, so `useImportType` and the unused-import rules would complain constantly without the override.
- **No Nuxt-specific rules.** Biome has no Nuxt domain — it just sees Vue. So things like "don't import from `#imports` directly" aren't enforced.
- **Avoid aggressive auto-fix on commit for `.vue` files.** Review template-adjacent rewrites before they land; the formatter can do surprising things inside templates.
- **Tailwind class sorting (`useSortedClasses`) is nursery + unsafe-fix.** It doesn't run on format-on-save, only on `biome check --write --unsafe`, and it doesn't recognize Tailwind plugin-defined utilities. I left it off; enable it later if you want it, but go in eyes open.

If any of those bite hard enough to hurt, the usual escape hatch is keeping Prettier for `.vue` only and letting Biome own `.ts`, `.css`, and `.json`. I'd try the all-Biome route first though — for most Nuxt codebases the override above is enough.
