# Biome configuration reference

Every key in `biome.json` / `biome.jsonc` with types and defaults. For CLI flag equivalents see `cli.md`.

Config files Biome will find (searched in order): `biome.json`, `biome.jsonc`, `.biome.json`, `.biome.jsonc`. Search starts in CWD / project root, walks up to filesystem root, then falls back to the user's config dir.

## Top-level shape

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "root": true,              // default true. Set false for nested configs.
  "extends": ["./shared.json"],  // or "//" to extend the project-root config.

  "files": { ... },
  "vcs": { ... },
  "formatter": { ... },
  "linter": { ... },
  "assist": { ... },

  "javascript": { ... },
  "json": { ... },
  "css": { ... },
  "graphql": { ... },
  "html": { ... },

  "overrides": [ ... ]
}
```

## `files`

```jsonc
{
  "files": {
    "includes": ["**"],       // glob patterns; negate with "!" (skip tools) or "!!" (also skip scanner)
    "ignoreUnknown": false,   // default false — unknown file types emit a diagnostic
    "maxSize": 1048576        // bytes; default 1 MiB. Larger files silently skipped.
  }
}
```

Glob rules:
- `*` matches any sequence **except `/`** (v2 change — was recursive in v1).
- `**` matches any sequence including `/`.
- `!` excludes from tool processing.
- `!!` additionally excludes from the project scanner (used by `domains.project` / `domains.types`).
- Negated globs must **follow** a positive match like `"**"`.
- Paths are relative to the config file's directory.

Protected files (Biome never emits diagnostics for these regardless of config): `composer.lock`, `npm-shrinkwrap.json`, `package-lock.json`, `yarn.lock`.

## `vcs`

```jsonc
{
  "vcs": {
    "enabled": false,         // default false. Must be true for --staged / --changed / useIgnoreFile.
    "clientKind": "git",
    "useIgnoreFile": false,   // respect .gitignore
    "root": ".",              // VCS root relative to config
    "defaultBranch": "main"   // used by --changed
  }
}
```

## `formatter` (global)

Options here apply to every language unless overridden under `javascript.formatter`, `json.formatter`, etc.

```jsonc
{
  "formatter": {
    "enabled": true,
    "formatWithErrors": false,  // format files that have parse errors
    "includes": [],             // narrow from files.includes
    "indentStyle": "tab",       // "tab" | "space" — default "tab"
    "indentWidth": 2,
    "lineEnding": "lf",         // "lf" | "crlf" | "cr" | "auto"
    "lineWidth": 80,
    "attributePosition": "auto",  // "auto" | "multiline"
    "bracketSpacing": true,
    "expand": "auto",           // "auto" | "always" | "never"
    "trailingNewline": true,
    "useEditorconfig": false    // respect .editorconfig when set
  }
}
```

## `linter` (global)

```jsonc
{
  "linter": {
    "enabled": true,
    "includes": [],
    "rules": {
      "recommended": true,
      // Group-level severity (shortcut):
      "style": "warn",
      "correctness": "error",
      // Individual rules:
      "suspicious": {
        "noDebugger": "off",
        "noExplicitAny": "warn",
        "useNamingConvention": {
          "level": "error",
          "fix": "none",                    // "safe" | "unsafe" | "none"
          "options": { "strictCase": false }
        }
      }
    },
    "domains": {
      "react": "recommended",    // "all" | "recommended" | "none" | "off"
      "next": "recommended",
      "vue": "recommended",
      "solid": "recommended",
      "qwik": "recommended",
      "react-native": "recommended",
      "test": "recommended",
      "drizzle": "recommended",
      "playwright": "recommended",
      "turborepo": "recommended",
      "project": "recommended",   // expensive: module-graph scanner
      "types": "recommended"      // expensive: type inference
    }
  }
}
```

Severity levels: `"error"` (fails CI), `"warn"`, `"info"`, `"off"`. In v2 many `style` rules default to `warn`, not `error`.

Domains auto-enable when their dependency is detected in `package.json`. You can still override them.

## `assist` (global)

```jsonc
{
  "assist": {
    "enabled": true,
    "includes": [],
    "actions": {
      "source": {
        "organizeImports": "on",        // "on" | "off" | {level, options}
        "useSortedKeys": "on",
        "useSortedProperties": "on",
        "useSortedInterfaceMembers": "on",
        "useSortedAttributes": "on"
      }
    }
  }
}
```

Assist was called `organizeImports` at the top level in v1. In v2 every source action is under `assist.actions.source.<name>`.

## `javascript`

```jsonc
{
  "javascript": {
    "parser": {
      "unsafeParameterDecoratorsEnabled": false,
      "jsxEverywhere": true
    },
    "formatter": {
      "enabled": true,
      "indentStyle": "space",       // override global
      "indentWidth": 4,
      "lineWidth": 120,
      "quoteStyle": "double",       // "double" | "single"
      "jsxQuoteStyle": "double",
      "quoteProperties": "asNeeded", // "asNeeded" | "preserve"
      "trailingCommas": "all",      // "all" | "es5" | "none"
      "semicolons": "always",       // "always" | "asNeeded"
      "arrowParentheses": "always", // "always" | "asNeeded"
      "bracketSameLine": false,
      "bracketSpacing": true,
      "attributePosition": "auto",
      "expand": "auto",
      "operatorLinebreak": "after", // "after" | "before"
      "trailingNewline": true
    },
    "linter": { "enabled": true, "includes": [] },
    "assist": { "enabled": true },
    "globals": ["fetch", "AbortController"],
    "jsxRuntime": "automatic",     // "automatic" | "classic"
    "experimentalEmbeddedSnippetsEnabled": false  // format CSS/GraphQL inside JS template literals
  }
}
```

## `json`

```jsonc
{
  "json": {
    "parser": {
      "allowComments": false,
      "allowTrailingCommas": false
    },
    "formatter": {
      "enabled": true,
      "trailingCommas": "none",      // "none" | "all"
      "expand": "auto",              // package.json defaults to "always"
      "bracketSpacing": true
    },
    "linter": { "enabled": true },
    "assist": { "enabled": true }
  }
}
```

Well-known JSON-ish files get parser flags set automatically — you don't need an override:
- **Strict JSON** (allowComments=false, allowTrailingCommas=false): `.all-contributorsrc`, `.bowerrc`, `.htmlhintrc`, `.jslintrc`, `.nycrc`, etc.
- **Comments only**: `.eslintrc.json`, `.ember-cli`, `.jscsrc`, `.jshintrc`, `tslint.json`, `turbo.json`.
- **Comments + trailing commas**: `.babelrc`, `.babelrc.json`, `.devcontainer.json`, `.hintrc`, `.oxlintrc.json`, `.swcrc`, `api-extractor.json`, `babel.config.json`, `deno.json`, `dprint.json`, `jsconfig.json`, `tsconfig.json`, etc.

## `css`

```jsonc
{
  "css": {
    "parser": {
      "cssModules": false,
      "tailwindDirectives": false    // enable for Tailwind v4 @theme / @apply / @utility / @variant / @source
    },
    "formatter": {
      "enabled": true,
      "quoteStyle": "double"         // "double" | "single"
    },
    "linter": { "enabled": true },
    "assist": { "enabled": true }
  }
}
```

## `graphql`

```jsonc
{
  "graphql": {
    "formatter": { "enabled": true, "quoteStyle": "double" },
    "linter": { "enabled": true },
    "assist": { "enabled": true }
  }
}
```

## `html`

```jsonc
{
  "html": {
    "formatter": {
      "enabled": true,
      "attributePosition": "auto",
      "bracketSameLine": false,
      "whitespaceSensitivity": "css",   // "css" | "strict" | "ignore"
      "indentScriptAndStyle": false,
      "selfCloseVoidElements": "never"  // "never" | "always"
    },
    "linter": { "enabled": true },
    "assist": { "enabled": true }
  }
}
```

`html.experimentalFullSupportEnabled: true` enables full HTML support (required for linting Vue/Svelte/Astro templates rigorously).

## `overrides`

Each entry in `overrides` is applied in order; later entries override earlier ones for matching files.

```jsonc
{
  "overrides": [
    {
      "includes": ["**/*.test.ts", "**/__tests__/**"],
      "linter": {
        "rules": {
          "suspicious": { "noExplicitAny": "off" }
        }
      }
    },
    {
      "includes": ["**/*.vue", "**/*.svelte", "**/*.astro"],
      "linter": {
        "rules": {
          "style": { "useConst": "off", "useImportType": "off" },
          "correctness": { "noUnusedVariables": "off", "noUnusedImports": "off" }
        }
      }
    },
    {
      "includes": ["**/*.jsonc"],
      "json": {
        "parser": { "allowComments": true, "allowTrailingCommas": true },
        "formatter": { "trailingCommas": "none" }
      }
    }
  ]
}
```

Any field available at the top level (formatter, linter, assist, javascript, json, css, graphql, html) is available inside an override.

## `extends` (monorepo)

Nested configs extend upward. In v2, use `root: false` plus `extends`. `"//"` is shorthand for "the project-root `biome.json`".

```jsonc
// apps/web/biome.jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.4.13/schema.json",
  "extends": "//",
  "root": false,
  "formatter": { "lineWidth": 120 }
}
```

Paths in `extends` resolve relative to the file that contains the `extends` (not to the file being extended).

You can also ship shared configs as npm packages:

```json
// @org/shared-configs/package.json
{ "name": "@org/shared-configs", "exports": { "./biome": "./biome.json" } }
```

```jsonc
// consumer biome.jsonc
{ "extends": ["@org/shared-configs/biome"] }
```

## Interaction with the scanner

Some rules need whole-project knowledge: import cycles, undeclared dependencies, type-aware diagnostics. Those are in the `project` and `types` domains and they trigger the scanner. The scanner walks everything that matches `files.includes` **unless** excluded with `!!`.

Rule of thumb: if a folder contains generated or vendored code that will never need diagnostics (`dist/`, `.nuxt/`, `node_modules`), exclude it with `!!` so the scanner skips it entirely. Use `!` only when you want the file indexed but not linted/formatted (e.g., `!**/*.generated.ts`).
