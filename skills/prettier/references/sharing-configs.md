# Sharing Prettier configurations

How to publish and consume a shared Prettier config as an npm package.

## Why share

In an organization with many repos, each repo maintaining its own `.prettierrc` means slow, inconsistent drift. A shared config package gives every repo the same formatting decisions with a single `pnpm update`.

## Package structure

```
@myorg/prettier-config/
├── package.json
└── index.js
```

### `package.json`

```json
{
  "name": "@myorg/prettier-config",
  "version": "1.0.0",
  "description": "Shared Prettier config for MyOrg",
  "type": "module",
  "exports": "./index.js",
  "files": ["index.js"],
  "peerDependencies": {
    "prettier": "^3.0.0"
  },
  "devDependencies": {
    "prettier": "^3.0.0"
  }
}
```

### `index.js`

```js
/** @type {import("prettier").Config} */
export default {
  printWidth: 100,
  semi: false,
  singleQuote: true,
  trailingComma: 'all',
}
```

Publish via `pnpm publish --access=public` (or keep private via your org's registry).

## Consuming a shared config

### Option 1: `"prettier"` key in `package.json`

```json
{
  "name": "consumer-project",
  "prettier": "@myorg/prettier-config"
}
```

Simplest — no config file needed.

### Option 2: `.prettierrc`

Just the package name as a string (JSON):

```json
"@myorg/prettier-config"
```

### Option 3: Extend and override (JS config)

```js
// prettier.config.mjs
import base from '@myorg/prettier-config'

export default {
  ...base,
  // override specific options:
  printWidth: 120,
}
```

## Shipping plugins with a shared config

If your shared config depends on a plugin (e.g. `prettier-plugin-tailwindcss`), list it as a dependency in the shared config's `package.json` and reference it in `index.js`:

```json
// @myorg/prettier-config/package.json
{
  "dependencies": {
    "prettier-plugin-tailwindcss": "^0.6.0"
  }
}
```

```js
// @myorg/prettier-config/index.js
import * as tailwind from 'prettier-plugin-tailwindcss'

/** @type {import("prettier").Config} */
export default {
  plugins: [tailwind],
  printWidth: 100,
  singleQuote: true,
}
```

Consumers get the plugin transitively — no separate install.

## Versioning strategy

Prettier output changes with plugin and Prettier versions. For a shared config, pick ONE of:

- **Pin exact versions.** The shared config bumps major version whenever it changes Prettier or plugin versions. Consumers are opt-in to formatting changes. Lots of PRs to update all repos in the org.
- **Float within minor.** The shared config uses caret ranges. Consumers can silently pull in new formatting after any `pnpm install`. Lower coordination cost; risk of surprise changes.

Most orgs pick the first and batch updates into quarterly "reformat everything" PRs.

## Using a shared config alongside repo-specific overrides

```js
// prettier.config.mjs in consumer repo
import shared from '@myorg/prettier-config'

export default {
  ...shared,
  // repo-specific overrides:
  printWidth: 120,
  overrides: [
    ...(shared.overrides ?? []),
    {
      files: '*.md',
      options: { proseWrap: 'always' },
    },
  ],
}
```

Always spread the shared `overrides` array if adding your own — otherwise the consumer override replaces (not extends) the shared ones.
