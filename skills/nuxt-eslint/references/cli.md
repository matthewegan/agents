# ESLint CLI reference (Nuxt context)

`@nuxt/eslint` doesn't ship its own CLI — you run the vanilla `eslint` CLI against a Nuxt-flavored flat config. This is the subset of flags that matter in a Nuxt project.

## Basic usage

```shell
eslint .                            # lint everything matching files.includes (from flat config)
eslint path/to/file.ts              # lint a single file
eslint src/                         # lint a directory
eslint '{app,server}/**/*.{ts,vue}' # lint an explicit glob (shell-expanded)
```

The trailing `.` is important — without an argument, ESLint errors out with "No files matching".

## Fixing

```shell
eslint . --fix                              # apply safe auto-fixes, overwrite files
eslint . --fix-dry-run                      # show what --fix would do without writing
eslint . --fix-type problem,suggestion      # limit fix types: directive, problem, suggestion, layout
```

Only rules whose fix is marked "safe" auto-apply. Rules with "suggestion"-level fixes require an explicit code action in the editor. ESLint does not have an "unsafe" tier like Biome — a fix is either safe (auto-applies) or a suggestion (manual).

## Reporting

```shell
eslint . --format=stylish            # default, human-readable
eslint . --format=compact
eslint . --format=unix
eslint . --format=json
eslint . --format=html -o report.html
```

ESLint 9 shipped only the built-in formatters above. **`junit`, `checkstyle`, `tap`, `jslint-xml`, and `visualstudio` are no longer in core** — install them as packages:

```shell
pnpm add -D eslint-formatter-junit
eslint . --format=junit -o eslint.junit.xml
```

If you forget to install and run `--format=junit`, ESLint fails with `The junit formatter is no longer part of core ESLint. Install it manually with npm install -D eslint-formatter-junit.`

GitHub Actions annotations need a third-party formatter (or parse JUnit). `reviewdog` and `eslint-formatter-github-annotations` are common picks.

## Caching

```shell
eslint . --cache                          # cache lint results in .eslintcache (project root)
eslint . --cache --cache-location=.cache/eslint
eslint . --cache --cache-strategy=content # default: 'metadata'. 'content' is more reliable across mtime changes.
```

Caching can cut rerun times by 5-20x on large repos. Use in CI if you have dep-aware caching available (e.g. GitHub Actions cache keyed on lockfile hash + source paths).

## Warnings / errors

```shell
eslint . --max-warnings=0                 # fail (exit 1) on any warning
eslint . --quiet                          # only show errors, drop warnings from output
eslint . --report-unused-disable-directives      # flag stale `// eslint-disable-*` comments as issues
eslint . --no-warn-ignored                # suppress "file ignored because of..." warnings
```

## Targeted runs

```shell
eslint . --rule 'no-console: error'        # ad-hoc rule for one run
eslint . --rulesdir ./my-rules             # local custom rules (rare with flat config)
eslint . --resolve-plugins-relative-to .
eslint . --no-eslintrc                     # ignore legacy eslintrc (not relevant for flat config)
```

With flat config, there's no `--config` flag equivalent for "extend from this external file." Instead, import and include in `eslint.config.mjs`.

## Explicit config path

```shell
eslint . --config eslint.config.mjs       # rarely needed; default resolution works
```

## Stdin

```shell
cat file.ts | eslint --stdin --stdin-filename=file.ts
```

Useful for editor integrations that want to lint an in-memory buffer.

## Common workflow recipes

### Pre-commit (via lint-staged)

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts,vue,jsx,tsx}": [
      "eslint --fix --no-warn-ignored --max-warnings=0"
    ]
  }
}
```

`--no-warn-ignored` silences "File ignored by .gitignore"-style warnings when lint-staged passes ignored files. `--max-warnings=0` stops the commit if warnings remain after `--fix`.

### CI

```shell
eslint . --max-warnings=0 --report-unused-disable-directives --format=junit -o eslint.junit.xml
```

Fail on warnings. Catch stale disable comments. Emit JUnit for the CI dashboard. Requires `eslint-formatter-junit` as a devDep (see "Reporting" above).

### Faster local feedback

```shell
eslint . --cache --quiet
```

`--cache` skips unchanged files. `--quiet` hides warnings, leaving only errors — cleaner output when iterating on a specific issue.

### Lint only staged files (outside lint-staged)

```shell
git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(js|ts|vue|tsx|jsx)$' | xargs eslint
```

### Lint only files changed vs. main

```shell
git diff origin/main... --name-only --diff-filter=ACMR | grep -E '\.(js|ts|vue|tsx|jsx)$' | xargs eslint
```

## Exit codes

- `0` — no errors (warnings may still be present unless `--max-warnings`)
- `1` — lint errors, or warnings when `--max-warnings` is set
- `2` — ESLint config error, CLI error, internal crash

## Environment variables

- `TIMING=1` — prints rule-by-rule timing info at the end of the run. Useful for finding slow rules.
- `DEBUG=eslint:*` — verbose internal debug logging.

## Speed troubleshooting

Slow lint? In order of likelihood:
1. **Type-aware rules.** If `config.typescript.tsconfigPath` is set, every run builds a TypeScript program. Disable for dev loops or move to CI-only.
2. **Large scan surface.** Check `files.includes` in `eslint.config.mjs` — accidentally scanning `node_modules` or `.nuxt` is common.
3. **No cache.** Add `--cache`.
4. **Many plugins.** `TIMING=1 eslint .` shows which rules dominate.
5. **Unicorn / complexity rules.** Individual rules can be slow; `TIMING=1` pinpoints them.
