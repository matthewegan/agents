# Prettier CLI reference

Every flag, exit codes, and common recipes.

## Basic usage

```shell
prettier [options] [file/dir/glob ...]
```

Most common:

```shell
prettier . --write             # format everything in place
prettier . --check             # CI mode — exit 1 if any file is unformatted
prettier . --list-different    # print filenames that need formatting
prettier src/ --write          # format just src/
prettier "src/**/*.ts" --write # glob (quote to prevent shell expansion!)
```

If you pass no path, Prettier exits with an error. Use `.` to mean "everything".

## Core flags

| Flag | Short | Effect |
|---|---|---|
| `--write` | `-w` | Overwrite files with formatted output |
| `--check` | `-c` | Fail (exit 1) if any file is unformatted; print count |
| `--list-different` | `-l` | Print unformatted filenames; exit 1 if any |
| `--ignore-unknown` | `-u` | Silently skip files Prettier can't parse |
| `--config <path>` | | Explicit config file path |
| `--no-config` | | Ignore any `.prettierrc*` |
| `--config-precedence <mode>` | | `cli-override` (default), `file-override`, `prefer-file` |
| `--ignore-path <path>` | | Alternate ignore file (default: `.prettierignore`, `.gitignore` is not auto-read) |
| `--with-node-modules` | | Include `node_modules` (normally ignored; almost never what you want) |
| `--cache` | | Cache results in `node_modules/.cache/prettier/` |
| `--cache-strategy <mode>` | | `metadata` (default, mtime+size) or `content` (hash) |
| `--log-level <level>` | | `silent` / `error` / `warn` / `log` (default) / `debug` |
| `--stdin-filepath <path>` | | When reading from stdin, path to infer parser from |
| `--no-error-on-unmatched-pattern` | | Don't fail when globs match nothing |
| `--no-plugin-search` | | Disable plugin auto-detection (faster if no plugins used) |

## Less common flags

| Flag | Effect |
|---|---|
| `--require-pragma` | Only format files with `/** @format */` or `@prettier` pragma |
| `--insert-pragma` | Insert `@format` pragma when formatting |
| `--check-ignore-pragma` | Skip files with `@noprettier` pragma |
| `--range-start <N>` | Only format a range of the file (needs stdin) |
| `--range-end <N>` | End of range |
| `--plugin <path>` | Load a plugin by path or package name |

## Option-as-flag overrides

Every config option can be set on the CLI by kebab-casing its name and prefixing with `--`:

```shell
prettier . --write --print-width 100 --single-quote --no-semi --trailing-comma all
```

Booleans: `--flag` enables, `--no-flag` disables.

Useful for one-off runs, but keep real config in `.prettierrc*` so everyone (and the editor extension) shares it.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Clean — everything formatted, or no files matched |
| `1` | Unformatted files found (with `--check` / `--list-different`) |
| `2` | Crash / configuration error / internal issue |

## Stdin

Read source from stdin, specify filename to infer parser, write formatted output to stdout:

```shell
cat src/foo.ts | prettier --stdin-filepath src/foo.ts > src/foo.formatted.ts
```

Editor integrations use this pattern.

## Caching

```shell
prettier . --cache --write
```

Stores hashes in `node_modules/.cache/prettier/.prettier-cache`. Subsequent runs skip unchanged files. Significant speedup on large repos.

Cache invalidates when:
- The Prettier version changes (binary hash differs).
- The file's own hash changes.
- But NOT when a plugin version changes — `rm -rf node_modules/.cache/prettier` after upgrading plugins.

`--cache-strategy content` uses file hash instead of mtime+size. Slightly slower but more reliable in CI where mtimes can lie.

## Recipes

### Format all project files on first adoption

```shell
prettier . --write
```

Commit the result in a single reformat-everything PR. Add the commit hash to a `.git-blame-ignore-revs` file so `git blame` skips it:

```
# .git-blame-ignore-revs
<sha of the reformat commit>
```

Configure git: `git config blame.ignoreRevsFile .git-blame-ignore-revs`.

### CI guard — fail on any unformatted file

```shell
prettier . --check
```

GitHub Actions:

```yaml
- run: npx prettier . --check
```

Bitbucket Pipelines:

```yaml
script:
  - pnpm exec prettier . --check
```

### Pre-commit (via lint-staged)

```json
// package.json
{
  "lint-staged": {
    "**/*": "prettier --write --ignore-unknown"
  }
}
```

`--ignore-unknown` lets lint-staged pass arbitrary file extensions without failing.

### Pre-commit (via lefthook)

```yaml
# lefthook.yml
pre-commit:
  commands:
    prettier:
      glob: "*.{js,ts,tsx,jsx,vue,css,scss,html,json,jsonc,md,yaml,yml,graphql}"
      run: npx prettier --write --ignore-unknown {staged_files}
      stage_fixed: true
```

### Format stdin (editor tools)

```shell
echo 'const x = 1;' | prettier --stdin-filepath a.ts
```

### Only format files changed vs. main

```shell
git diff origin/main... --name-only --diff-filter=ACMR \
  | xargs -r prettier --write --ignore-unknown
```

### Check formatting on only staged files (outside lint-staged)

```shell
git diff --cached --name-only --diff-filter=ACMR \
  | xargs -r prettier --check
```

### Dry run — see what would change

```shell
prettier . --list-different
# prints the files that would be reformatted; exit 1 if any
```

Or a full diff preview per file:

```shell
for f in $(prettier . --list-different); do
  diff -u "$f" <(prettier "$f")
done
```

### Targeted format with explicit config

```shell
prettier --config ./special.prettierrc.json "legacy/**/*.js" --write
```

## Troubleshooting

**"No parser could be inferred for file ..."**

Prettier doesn't know how to parse this file. Fixes:
- If the file has a non-standard extension, set `parser` in an `overrides` entry.
- If it's a file Prettier shouldn't touch, add to `.prettierignore`.
- Use `--ignore-unknown` to silently skip.

**"ENOENT: no such file or directory, open ...prettierrc..."**

The config resolution found a broken config file path (often a symlink pointing at a deleted file). Run `prettier --find-config-path <somefile>` to see which config Prettier is picking up.

**"Files are ignored ..."**

A file in your glob matched `.prettierignore`. Either remove it from the ignore list or drop the file from your arguments.

**Slow**

Add `--cache`. Check for large generated files Prettier is re-parsing every run.

**Format keeps flipping on Windows**

Ensure `endOfLine: "lf"` in `.prettierrc` and `.gitattributes: * text=auto eol=lf` at repo root.
