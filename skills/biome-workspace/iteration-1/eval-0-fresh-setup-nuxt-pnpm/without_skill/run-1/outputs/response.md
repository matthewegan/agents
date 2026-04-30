# Biome setup for your Nuxt 4 + pnpm project

Below is a project-specific `biome.jsonc` and the `package.json` scripts to add. After you run `pnpm add -D -E @biomejs/biome`, drop these in and you're set.

## `biome.jsonc`

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
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
      "!**/node_modules",
      "!**/.nuxt",
      "!**/.output",
      "!**/.data",
      "!**/dist",
      "!**/coverage",
      "!**/.nitro",
      "!**/.cache",
      "!**/drizzle",
      "!**/*.min.js",
      "!**/*.min.css",
      "!pnpm-lock.yaml"
    ]
  },
  "formatter": {
    "enabled": true,
    "useEditorconfig": false,
    "formatWithErrors": false,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100,
    "lineEnding": "lf"
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "jsxQuoteStyle": "double",
      "semicolons": "asNeeded",
      "trailingCommas": "all",
      "arrowParentheses": "always",
      "bracketSameLine": false,
      "bracketSpacing": true,
      "quoteProperties": "asNeeded"
    }
  },
  "json": {
    "formatter": {
      "enabled": true,
      "trailingCommas": "none"
    },
    "parser": {
      "allowComments": true,
      "allowTrailingCommas": true
    }
  },
  "css": {
    // Tailwind v4 uses @theme, @utility, @variant, @custom-variant, @apply, @source, etc.
    // Biome's CSS parser accepts at-rules it doesn't know about, so these pass through fine.
    "formatter": {
      "enabled": true,
      "quoteStyle": "single"
    },
    "parser": {
      "cssModules": false
    },
    "linter": {
      "enabled": true
    }
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "style": {
        "useConst": "error",
        "useTemplate": "error",
        "noUselessElse": "warn",
        "useNodejsImportProtocol": "error"
      },
      "suspicious": {
        "noExplicitAny": "warn",
        "noConsole": {
          "level": "warn",
          "options": { "allow": ["warn", "error", "info"] }
        }
      },
      "correctness": {
        "noUnusedVariables": "warn",
        "noUnusedImports": "warn"
      },
      "complexity": {
        "noForEach": "off"
      },
      "a11y": {
        // Nuxt/Vue templates are not analyzed by Biome; a11y rules mostly target JSX.
        "recommended": true
      }
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
      // Vue SFCs: Biome 2.x parses <script lang="ts"> blocks but does NOT format <template> or <style>.
      // Keep the script formatter aligned with our TS settings; skip linting rules that don't
      // understand Vue's compiler macros or template-only usage so we don't get false positives.
      "includes": ["**/*.vue"],
      "linter": {
        "rules": {
          "correctness": {
            // defineProps/defineEmits/useRoute/etc. are auto-imported by Nuxt; Biome can't see that.
            "noUndeclaredVariables": "off",
            // Composables and components used only in <template> look unused to Biome.
            "noUnusedVariables": "off",
            "noUnusedImports": "off"
          },
          "style": {
            // <script setup> top-level consts are "exported" via the compiler — don't flag them.
            "useImportType": "off"
          }
        }
      }
    },
    {
      // Nuxt auto-imports (composables, components, server utils) are resolved at build time.
      "includes": ["app/**/*.ts", "app/**/*.vue", "server/**/*.ts", "composables/**/*.ts"],
      "linter": {
        "rules": {
          "correctness": {
            "noUndeclaredVariables": "off"
          }
        }
      }
    },
    {
      // Config files often need default exports, console output, and CJS-ish patterns.
      "includes": [
        "nuxt.config.ts",
        "drizzle.config.ts",
        "*.config.ts",
        "*.config.js",
        "*.config.mjs"
      ],
      "linter": {
        "rules": {
          "suspicious": {
            "noConsole": "off"
          },
          "style": {
            "noDefaultExport": "off"
          }
        }
      }
    },
    {
      // Drizzle migrations are generated SQL-ish TS — don't fight the generator.
      "includes": ["server/database/migrations/**", "drizzle/**"],
      "formatter": { "enabled": false },
      "linter": { "enabled": false }
    }
  ]
}
```

## `package.json` scripts

Merge these into your existing `scripts` block:

```json
{
  "scripts": {
    "format": "biome format --write .",
    "format:check": "biome format .",
    "lint": "biome lint .",
    "lint:fix": "biome lint --write .",
    "check": "biome check .",
    "check:fix": "biome check --write .",
    "check:ci": "biome ci ."
  }
}
```

Day-to-day you'll mostly use `pnpm check:fix` (format + lint + organize imports, all in one pass). `pnpm check:ci` is the non-writing, CI-friendly variant that also enforces no pending diagnostics.

## Heads-up about Biome's Vue support

A few things that will bite you if you don't know them up front:

- **Biome formats the `<script>` block of SFCs, not `<template>` or `<style>`.** As of Biome 2.x there is partial Vue support: it extracts and formats/lints the JS/TS inside `<script>` and `<script setup>`, but the template markup and `<style>` blocks are untouched. If you want template formatting, you'll still need Prettier (or the Volar/Vue-official formatter in your editor) for that portion. Running `biome format` on a `.vue` file is safe — it just leaves the non-script sections alone.
- **Auto-imports look like undeclared variables.** Nuxt auto-imports (`ref`, `computed`, `useRoute`, `useFetch`, your `server/utils/*` exports, components, etc.) aren't visible to Biome's resolver, so rules like `noUndeclaredVariables` and `noUnusedImports` will false-positive. The overrides in the config above disable those for `.vue` and the Nuxt-aware directories. If you'd rather keep the rules on, add a Biome-compatible globals declaration or run `nuxi prepare` first and point Biome at `.nuxt/types/` — but the override approach is simpler and what I'd recommend.
- **Compiler macros (`defineProps`, `defineEmits`, `defineModel`, etc.) are globals** injected by the Vue compiler. Same story as above — the override disables the rules that would flag them.
- **Template-only usage isn't seen.** A `const foo = ref(0)` in `<script setup>` used only in `<template>` will look unused to Biome. That's why `noUnusedVariables` is off for `.vue` files.
- **TailwindCSS v4 classes and `@theme`/`@utility`/`@apply` directives are fine.** Biome's CSS parser tolerates unknown at-rules, and it has no class-name linter, so nothing to configure there. If you later want Tailwind class sorting, Biome's `useSortedClasses` rule exists but is nursery/experimental — I left it off.
- **No Biome plugin for Vue template linting exists yet.** If template-level linting matters to you (e.g., `vue/no-unused-vars` in template), keep `eslint-plugin-vue` around alongside Biome and scope ESLint to `*.vue` templates only. Otherwise, Biome alone is fine for 90% of a Nuxt project.

TL;DR: Biome will handle all your `.ts` and `.css` perfectly, and the `<script>` portion of `.vue` files. The template and style blocks are on their own — rely on your editor's Vue tooling for those.
