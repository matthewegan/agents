# Migration paths

Three common starting points: community `@nuxtjs/eslint-module`, legacy `.eslintrc*`, or nothing at all.

## From `@nuxtjs/eslint-module` (old community module)

The old community module (`@nuxtjs/eslint-module`, from `nuxt-modules/eslint`) is superseded by the official `@nuxt/eslint`. They're different packages.

**Steps:**

```shell
# 1. Remove old module
pnpm remove @nuxtjs/eslint-module

# 2. Install the official one
npx nuxt module add eslint
# (installs @nuxt/eslint and registers it in nuxt.config.ts)
```

**Update `nuxt.config.ts`:**

```diff
 export default defineNuxtConfig({
   modules: [
-    '@nuxtjs/eslint-module',
+    '@nuxt/eslint',
   ],
-  eslintConfig: { /* old options */ },
+  eslint: {
+    // new options — see configuration.md
+    checker: true,  // if you want the old behavior (dev-server lint)
+  },
 })
```

**If you were using the dev-server checker:** install the peer plugin yourself now.

```shell
pnpm add -D vite-plugin-eslint2
```

**Delete your existing ESLint config** (`.eslintrc.*`) — see next section.

## From legacy `.eslintrc*` to flat config

The new module only supports flat config (ESLint's default format as of v9). Legacy files are ignored.

**Steps:**

1. Back up your old config:
   ```shell
   cp .eslintrc.json .eslintrc.json.bak  # or whatever variant you have
   ```

2. Install `@nuxt/eslint`:
   ```shell
   npx nuxt module add eslint
   ```
   On next `nuxt prepare` (or `nuxt dev`), `eslint.config.mjs` gets generated.

3. Port custom rules from the old config into `eslint.config.mjs`:

   ```js
   // eslint.config.mjs
   import withNuxt from './.nuxt/eslint.config.mjs'

   export default withNuxt(
     // Old .eslintrc rules go here as a flat-config entry:
     {
       rules: {
         // your old rules, usually identical in flat config
         'no-console': 'warn',
         '@typescript-eslint/no-explicit-any': 'off',
       }
     },
     // If you had a path-specific `overrides` block, translate each one:
     {
       files: ['**/*.test.ts'],
       rules: { /* ... */ }
     }
   )
   ```

4. Port `extends` — each ESLint extends-reference becomes a flat-config import:

   ```js
   // Old:
   //   "extends": ["@antfu", "plugin:react/recommended"]

   // Flat config:
   import antfu from '@antfu/eslint-config'
   import react from 'eslint-plugin-react/configs/recommended.js'
   import withNuxt from './.nuxt/eslint.config.mjs'

   export default withNuxt(
     antfu({ /* ... */ }),
     react
   )
   ```

   If your `extends` was just `nuxt`-flavored stuff, drop it entirely — `@nuxt/eslint` replaces it.

5. Delete the legacy files:
   ```shell
   rm .eslintrc .eslintrc.json .eslintrc.js .eslintrc.yml .eslintrc.yaml 2>/dev/null
   rm .eslintignore 2>/dev/null
   ```

6. Run `eslint .` to catch anything that needs adjustment.

### Key flat-config differences vs legacy

| Legacy | Flat config |
|---|---|
| `extends` field | Import + include in array |
| `overrides` field | Separate config entries with `files` |
| `env` field | `languageOptions.globals` (usually set by `@nuxt/eslint`) |
| `parserOptions` | `languageOptions.parserOptions` |
| `plugins` as strings | Imported plugin objects under `plugins: { 'my-plugin': plugin }` |
| `.eslintignore` | `ignores` field inside a config entry, or `files.includes` negation |
| Rule names like `'@typescript-eslint/no-...'` | Same — names don't change |

### Migrating an `.eslintignore`

Old:
```
dist
**/*.generated.ts
```

New — in `eslint.config.mjs`:

```js
export default withNuxt()
  .prepend({
    ignores: ['dist/**', '**/*.generated.ts']
  })
```

## From nothing (fresh Nuxt project)

```shell
npx nuxt module add eslint
```

Done. On next `nuxt prepare`, `eslint.config.mjs` is generated. Add scripts:

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

Optional add-ons:
- Prettier: `pnpm add -D -E prettier` + `.prettierrc.json` (see `prettier` skill).
- lint-staged / lefthook pre-commit hook.

## From a non-Nuxt ESLint setup to a Nuxt one

If you have an existing ESLint setup (e.g. `@antfu/eslint-config`) and are adding Nuxt later:

1. Install module: `npx nuxt module add eslint`.
2. Disable Nuxt's own preset so your existing config owns rules:
   ```ts
   // nuxt.config.ts
   eslint: { config: { standalone: false } }
   ```
3. Combine in `eslint.config.mjs`:
   ```js
   import antfu from '@antfu/eslint-config'
   import withNuxt from './.nuxt/eslint.config.mjs'

   export default withNuxt(
     antfu({ vue: true, typescript: true })
   )
   ```

`@nuxt/eslint` still contributes Nuxt-specific rules (`nuxt/prefer-import-meta`, etc.) and the auto-imports-aware globals, but the JS/TS/Vue rule set comes from antfu.

## Post-migration checklist

- [ ] `nuxt prepare` runs clean and generates `.nuxt/eslint.config.mjs`.
- [ ] `eslint .` runs without "Parsing error" on the entire tree.
- [ ] VS Code ESLint extension shows squigglies (install / update if not).
- [ ] Pre-commit hook / lint-staged config updated to call `eslint` not any old wrapper.
- [ ] CI workflow updated — add `nuxt prepare` step before `eslint .`.
- [ ] `.eslintrc*` + `.eslintignore` deleted from the repo.
- [ ] Old module (`@nuxtjs/eslint-module` or similar) removed from `package.json`.
- [ ] If using Prettier: `config.stylistic: false` (the default) and `eslint-config-prettier` unused (redundant).
