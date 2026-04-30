# Prettier options reference

Every option Prettier v3 supports, with defaults, accepted values, and what changes. Uncommon options are toward the bottom.

## Common — tune these

### `printWidth` (number, default `80`)

Desired line length. Prettier tries to wrap at this limit but will wrap earlier or later for readability. Common project values: `80`, `100`, `120`. Don't set higher than ~140 — Prettier's wrapping heuristics assume moderate widths.

### `tabWidth` (number, default `2`)

Number of spaces per indent level. `2` is near-universal. `4` for teams that prefer it.

### `useTabs` (boolean, default `false`)

Use tabs for indentation. When `true`, `tabWidth` is informational (editors still decide tab display width).

### `semi` (boolean, default `true`)

Print semicolons at the ends of statements. `false` = "no-semi" style (Prettier inserts `;` only where required to avoid ASI hazards).

### `singleQuote` (boolean, default `false`)

Use single quotes in JS/TS string literals. Doesn't affect JSX — see `jsxSingleQuote`.

### `jsxSingleQuote` (boolean, default `false`)

Use single quotes in JSX attributes. Typical setting: keep `false` even when `singleQuote: true` (standard convention is single quotes in JS, double quotes in JSX/HTML attributes).

### `quoteProps` (`"as-needed" | "consistent" | "preserve"`, default `"as-needed"`)

When to quote object keys.
- `"as-needed"`: `{ foo: 1, 'bar-baz': 2 }`
- `"consistent"`: if any key needs quotes, quote them all.
- `"preserve"`: keep the original.

### `trailingComma` (`"all" | "es5" | "none"`, default `"all"`)

Trailing commas in multiline arrays / objects / parameters.
- `"all"` — everywhere, including function parameters. Requires ES2017+. **Default in v3**.
- `"es5"` — places where ES5 supports them (arrays, objects). Not function params.
- `"none"` — nowhere. Rarely chosen.

"Magic trailing comma": a trailing comma in a multi-line literal signals "keep multi-line". Removing it lets Prettier collapse short literals to one line.

### `bracketSpacing` (boolean, default `true`)

Spaces inside object literal braces: `{ foo: 1 }` vs `{foo: 1}`.

### `bracketSameLine` (boolean, default `false`)

For multi-line HTML/JSX elements, put the closing `>` on the same line as the last attribute. `true` is the compact style; `false` puts `>` on its own line.

### `arrowParens` (`"always" | "avoid"`, default `"always"`)

Parens around sole arrow parameter.
- `"always"` — `(x) => x + 1`
- `"avoid"` — `x => x + 1`

### `endOfLine` (`"lf" | "crlf" | "cr" | "auto"`, default `"lf"`)

Line ending.
- `"lf"` — Unix (recommended; **default in v3**).
- `"crlf"` — Windows.
- `"cr"` — classic Mac. Almost nobody.
- `"auto"` — match what git already has. Dangerous in mixed OS teams; avoid.

Pair with `.gitattributes: * text=auto eol=lf` to prevent Windows CRLF flip-flopping.

### `proseWrap` (`"always" | "never" | "preserve"`, default `"preserve"`)

Markdown/MDX wrapping behavior.
- `"preserve"` — don't rewrap prose.
- `"always"` — wrap at `printWidth`.
- `"never"` — never wrap.

For long-form docs, `"always"` + `printWidth: 80` is common. For README-style where authors manually break lines, `"preserve"` is better.

### `htmlWhitespaceSensitivity` (`"css" | "strict" | "ignore"`, default `"css"`)

How HTML formatting treats whitespace.
- `"css"` — respects CSS `display` property to decide whether whitespace is meaningful.
- `"strict"` — all whitespace is significant.
- `"ignore"` — all whitespace is insignificant.

### `vueIndentScriptAndStyle` (boolean, default `false`)

Indent `<script>` and `<style>` bodies inside Vue SFCs. Most Vue teams keep this `false` — code starts at column 0, matching most style guides.

### `singleAttributePerLine` (boolean, default `false`)

Force one attribute per line in HTML / JSX / Vue templates. Useful for forms / components with many attributes.

### `embeddedLanguageFormatting` (`"auto" | "off"`, default `"auto"`)

Format code embedded in template literals when Prettier can identify the language (e.g. `html\`…\``, `css\`…\``, `graphql\`…\``). Set to `"off"` if embedded detection misidentifies something.

### `experimentalTernaries` (boolean, default `false`)

Alternate ternary formatting that groups related branches. Cleaner on complex nested ternaries. Stable enough to enable.

### `experimentalOperatorPosition` (`"start" | "end"`, default `"end"`)

Whether to place operators at the start or end of wrapped lines (e.g. `&&`, `+`). `"end"` is the classic Prettier style; `"start"` is the "leading-operator" style some teams prefer.

## Config-file-level — rarely tuned

### `parser` (string, auto-detected)

Override the parser. Usually inferred from file extension. Only set inside `overrides[].options` for obscure filenames (e.g. `.prettierrc` itself):

```json
{
  "overrides": [
    { "files": ".prettierrc", "options": { "parser": "json" } }
  ]
}
```

Never set at the top level — breaks auto-detection.

### `filepath` (string)

Used with `--stdin`. Tells Prettier which parser to use for stdin input. Prefer `--stdin-filepath` on the CLI.

### `requirePragma` (boolean, default `false`)

Only format files that contain an `@format` or `@prettier` comment. Useful to roll out Prettier file-by-file on legacy repos.

### `insertPragma` (boolean, default `false`)

When formatting, insert `@format` at the top of the file. Works with `requirePragma` for opt-in formatting.

### `checkIgnorePragma` (boolean, default `false`)

Skip files that contain `@noprettier` in their top comment.

### `htmlFormat` (Prettier 3.3+)

Handled via parser selection, not a separate option.

## Overrides by glob

`overrides` lets any of the above apply differently per path:

```json
{
  "semi": false,
  "overrides": [
    {
      "files": "*.md",
      "options": { "printWidth": 80, "proseWrap": "always" }
    },
    {
      "files": ["*.yml", "*.yaml"],
      "options": { "singleQuote": false }
    },
    {
      "files": ["legacy/**"],
      "options": { "semi": true, "trailingComma": "es5" }
    }
  ]
}
```

Later override entries win over earlier ones.

## Parser-by-extension map

Prettier infers the parser from the file extension. Here's the default mapping:

| Extension | Parser |
|---|---|
| `.js`, `.cjs`, `.mjs` | `babel` |
| `.jsx` | `babel` (with JSX) |
| `.ts`, `.cts`, `.mts` | `typescript` |
| `.tsx` | `typescript` (with JSX) |
| `.vue` | `vue` (handles template + script + style) |
| `.css` | `css` |
| `.scss` | `scss` |
| `.less` | `less` |
| `.html`, `.htm` | `html` |
| `.json` | `json` |
| `.jsonc` | `json5` |
| `.json5` | `json5` |
| `.yaml`, `.yml` | `yaml` |
| `.graphql`, `.gql` | `graphql` |
| `.md` | `markdown` |
| `.mdx` | `mdx` |
| `.hbs`, `.handlebars` | `glimmer` |

Plugins can register more parsers (e.g. `prettier-plugin-tailwindcss` augments JSX/Vue/HTML parsers).

## Defaults changed between v2 and v3

| Option | v2 default | v3 default |
|---|---|---|
| `trailingComma` | `"es5"` | `"all"` |
| `endOfLine` | `"auto"` | `"lf"` |

If you had a v2 project without explicit values, running Prettier v3 on it may reformat many files. Either:
- Accept the new defaults and commit the reformat in a single PR.
- Pin the old values in `.prettierrc.json`.

## "Why doesn't Prettier have option X?"

See [Prettier's `option-philosophy.md`](https://prettier.io/docs/en/option-philosophy). Short version: Prettier deliberately avoids adding options because each one creates another thing for teams to argue about. If you want heavy customization, the answer is probably another formatter — Prettier is opinionated by design.
