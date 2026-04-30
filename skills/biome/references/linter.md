# Biome linter reference

Rule groups, severity model, fix controls, domains, and suppression. The full list of 400+ rules lives at https://biomejs.dev/linter/rules; this file covers patterns and noteworthy rules.

## Rule groups

Every rule belongs to exactly one group. Rule IDs are `lint/<group>/<ruleName>`.

| Group | Default severity* | What it catches |
|---|---|---|
| `correctness` | mixed (many `error`) | Almost-certainly bugs — unused variables, invalid regex, unreachable code, wrong hook usage. |
| `suspicious` | mixed | Looks wrong but sometimes intentional — `any`, `console.log`, `==`, `async` without `await`. |
| `style` | `warn` | Consistency — `const` vs `let`, `import type`, naming conventions. |
| `complexity` | mixed | Overwrought code — useless fragments, redundant conditions, excessive nesting. |
| `performance` | mixed | Slow patterns — `.forEach` in hot loops, barrel re-imports, accumulating spreads. |
| `security` | `error` | Obvious security footguns — `eval`, unsafe HTML injection, weak crypto. |
| `a11y` | mixed | Accessibility — missing alt text, unlabeled buttons, interactive role misuse. |
| `nursery` | `info`/`off` | Experimental rules. Names, semantics, and defaults can change in any minor release. |

\* Defaults vary per-rule inside each group. When `recommended: true` is on, each recommended rule's own default severity applies. Check `biome explain lint/<group>/<name>` or the rule docs for a specific one.

## Configuring rules

```jsonc
{
  "linter": {
    "rules": {
      "recommended": true,
      // 1) Whole-group shortcut
      "style": "warn",
      "correctness": "error",
      // 2) Individual rule toggles
      "suspicious": {
        "noDebugger": "off",
        "noExplicitAny": "warn",
        // 3) Full rule object — level, fix strategy, options
        "useNamingConvention": {
          "level": "error",
          "fix": "none",                      // "safe" | "unsafe" | "none"
          "options": { "strictCase": false }
        }
      }
    }
  }
}
```

Severity levels:
- `"error"` — Fails `biome ci` and `biome check`.
- `"warn"` — Surfaced but doesn't fail unless `--error-on-warnings`.
- `"info"` — Informational.
- `"off"` — Disabled.

`"fix"` on a rule controls what `--write` does:
- `"safe"` — apply safe fix on `--write`.
- `"unsafe"` — only apply on `--write --unsafe`.
- `"none"` — never auto-fix, even though the rule has a fix available. Useful when a fix is noisy (e.g., `noUnusedVariables` prefixing vars with `_`).

## Safe vs. unsafe fixes

Biome categorizes every fix:
- **Safe** — never changes runtime semantics. Editors apply these on save.
- **Unsafe** — may change semantics (e.g., `==` → `===`, reassignment-dead `let` → `const`). Run `biome check --write --unsafe` and review the diff.

Rule docs label each rule's fix. When you run `--write`, only safe fixes apply. `--unsafe` adds the unsafe ones.

## Domains

Domains are bundled rule sets tied to a library/framework. Biome auto-enables a domain when it detects the corresponding package in `package.json`; you can also enable them explicitly.

| Domain | Triggered by | What it enables |
|---|---|---|
| `react` | `react ≥ 16` | Hooks (`useExhaustiveDependencies`, `useHookAtTopLevel`), JSX (`useJsxKeyInIterable`, `noChildrenProp`), perf (`noNestedComponentDefinitions`). |
| `next` | `next ≥ 14` | Next.js image/script/async-component/head rules. Extends `react`. |
| `vue` | `vue ≥ 3` | Vue template + directive rules. |
| `solid` | `solid ≥ 1` | Destructured-props rules, signals. |
| `qwik` | `@builder.io/qwik ≥ 1` | Qwik-specific rules. |
| `react-native` | `react-native ≥ 0.60` | RN-specific style + platform API rules. |
| `test` | `jest`, `vitest`, `mocha`, `ava` | Test helper rules, `noFocusedTests`, `noDisabledTests`. |
| `drizzle` | `drizzle-orm ≥ 0.9` | ORM-specific correctness rules. |
| `playwright` | `@playwright/test ≥ 1` | Playwright test rules. |
| `turborepo` | `turbo ≥ 1` | Turborepo pipeline rules. |
| `project` | n/a (opt-in) | Module-graph rules: `noImportCycles`, `noUndeclaredDependencies`, etc. **Expensive.** |
| `types` | n/a (opt-in) | Type-aware rules: `noFloatingPromises`, `noMisusedPromises`. **Expensive** — runs type inference. |

Opt in with:

```jsonc
{
  "linter": {
    "domains": {
      "react": "recommended",
      "project": "recommended"
    }
  }
}
```

Values: `"all"`, `"recommended"`, `"none"`, `"off"`.

**Performance note.** `project` and `types` enable the scanner which builds a module graph and infers types across the whole repo. On ~2k-file projects this adds ~1s; on ~5k-file projects ~5-7s. Don't enable unless you want the specific rules they unlock.

## Suppression syntax

Every suppression requires a reason — Biome flags un-reasoned suppressions as diagnostics.

```ts
// Line-level (applies to the next statement)
// biome-ignore lint/suspicious/noExplicitAny: third-party types lie here
const fromLibrary: any = sdk.call()

// Whole-file (put at top of file)
// biome-ignore-all lint/suspicious/noExplicitAny: generated file

// Formatter — disables formatting on the next node
// biome-ignore format: keep this aligned manually
const matrix = [
  1, 2, 3,
  4, 5, 6,
]
```

Categories that can be suppressed: `lint/<group>/<ruleName>`, `lint/<group>` (whole group), `format`, `assist/<action>`.

## Noteworthy rules

### `suspicious/noExplicitAny`
- Recommended, warn by default.
- Triggers a lot on legacy code. Common to demote to `"warn"` or scope with an override for `**/generated/**`, `**/*.d.ts`.

### `style/noNonNullAssertion`
- Warns on `foo!`. Often demoted in TypeScript projects that use non-null assertions deliberately.

### `style/useImportType` / `style/useExportType`
- Enforces `import type { ... }` for type-only imports. Unsafe fix.

### `correctness/noUnusedVariables` / `correctness/noUnusedImports`
- Recommended. Unsafe fix (prefixes variables with `_`, removes imports).
- In Vue/Svelte/Astro files without full HTML support, this produces false positives — disable via overrides.

### `complexity/useOptionalChain`
- Suggests `a?.b` over `a && a.b`. Unsafe fix in edge cases.

### `style/useConst`
- `let` → `const` when never reassigned. Unsafe fix.

### `suspicious/noImplicitAnyLet`
- TypeScript: forbids `let x` with no type annotation and no initializer.

### `correctness/useParseIntRadix`
- Requires a radix on `parseInt(str, 10)`.

### `style/useNodejsImportProtocol`
- Requires `node:` prefix for Node built-ins (`node:fs` not `fs`).

### `nursery/useSortedClasses` (Tailwind class sorting)
- Sorts utility classes like `prettier-plugin-tailwindcss`. **Nursery** (unstable) and **unsafe fix**.
- Caveats: default Tailwind config only (no plugin utilities/variants), no screen-variant sort, no object-property sort in `clsx`/`cva` calls — those are configurable via `functions` option but still limited.
- Runs as a lint rule, not a formatter — editor "format on save" does **not** apply it.

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

### `a11y/useValidAnchor`
- Catches `<a href="#">` and anchors used as buttons.

### `security/noDangerouslySetInnerHtml`
- Forbids the React prop known for enabling XSS.

## Filtering on the CLI

```shell
# Run only a specific rule
biome lint --only=lint/suspicious/noExplicitAny

# Run only a group
biome lint --only=correctness

# Run only a domain
biome lint --only=react

# Skip wins over only
biome lint --skip=style --skip=lint/suspicious/noConsole
```

## Common tuning recipes

### Quiet the noise when adopting Biome on a legacy codebase

```jsonc
{
  "linter": {
    "rules": {
      "recommended": true,
      "suspicious": {
        "noExplicitAny": "off",
        "noImplicitAnyLet": "off"
      },
      "style": {
        "noNonNullAssertion": "off",
        "useImportType": "warn",
        "useConst": "warn"
      }
    }
  }
}
```

Turn them back on incrementally once the existing backlog is cleaned up.

### Test files allow magic numbers and `any`

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

### Generated files are off-limits

```jsonc
{
  "files": {
    "includes": ["**", "!**/*.generated.ts", "!!**/dist"]
  }
}
```

`!` = skip linting/formatting but still indexed by the scanner. `!!` = not even indexed.
