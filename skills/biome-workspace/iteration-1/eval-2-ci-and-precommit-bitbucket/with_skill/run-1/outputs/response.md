# Wiring Biome into lefthook + Bitbucket Pipelines

Three small pieces: a lefthook hook, a Pipelines step, and a `vcs` block in `biome.jsonc`. The `vcs` block is the load-bearing bit — without it, neither `--staged` nor `--changed` works.

## 1. Pre-commit hook (`lefthook.yml`)

```yaml
pre-commit:
  parallel: true
  commands:
    biome:
      glob: "*.{js,ts,cjs,mjs,jsx,tsx,json,jsonc,css,graphql,gql}"
      run: npx @biomejs/biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true
```

Install hooks with `npx lefthook install` (add it to a `postinstall` script if you want it automatic).

Why each flag:

- `check` (not `ci`) — `ci` refuses `--write`; a pre-commit hook needs to apply fixes.
- `--write` — apply safe formatter + lint fixes. No `--unsafe`: unsafe fixes can change runtime behavior (e.g. `==` → `===`) and shouldn't land silently on commit.
- `{staged_files}` — lefthook's built-in variable, pre-filtered by the `glob`.
- `--no-errors-on-unmatched` — if the filter drops every file, Biome would otherwise exit non-zero and block the commit.
- `--files-ignore-unknown=true` — defense in depth; if the glob ever lets something weird through, Biome just skips it.
- `stage_fixed: true` — lefthook re-adds files Biome rewrote so the fixes are part of the commit, not a phantom dirty tree afterward.

## 2. Bitbucket Pipelines (`bitbucket-pipelines.yml`)

```yaml
image: node:22

definitions:
  caches:
    pnpm: $BITBUCKET_CLONE_DIR/.pnpm-store

  steps:
    - step: &biome-ci
        name: Biome
        caches: [node, pnpm]
        clone:
          depth: full
        script:
          - corepack enable && corepack prepare pnpm@latest --activate
          - pnpm install --frozen-lockfile
          - git fetch --no-tags origin "+refs/heads/${BITBUCKET_PR_DESTINATION_BRANCH}:refs/remotes/origin/${BITBUCKET_PR_DESTINATION_BRANCH}"
          - >
            pnpm exec biome ci .
            --changed
            --since=origin/${BITBUCKET_PR_DESTINATION_BRANCH}
            --reporter=junit
            --reporter-file=test-reports/biome.junit.xml
        artifacts:
          - test-reports/biome.junit.xml

pipelines:
  pull-requests:
    '**':
      - step: *biome-ci
```

Key points:

- `biome ci` (not `biome check`) — read-only, rejects `--write`, and has the CI-specific reporters you need.
- `--reporter=junit --reporter-file=test-reports/biome.junit.xml` — Bitbucket Pipelines auto-discovers JUnit XML under `test-reports/**/*.xml` and renders results on the PR page (failed tests, affected files). The `artifacts` entry additionally lets you download the raw file from the pipeline.
- `--changed --since=origin/${BITBUCKET_PR_DESTINATION_BRANCH}` — limits Biome to only the files touched in this PR, which keeps run time proportional to the diff, not the repo.
- `pipelines.pull-requests: '**'` — runs on every PR regardless of source branch.
- Swap `pnpm`/`corepack` for `npm ci` / `yarn install --immutable` if that's your package manager; everything else stays the same.

## 3. `biome.jsonc` patch

```jsonc
{
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  }
}
```

That's the only thing you have to add. The rest of your `biome.jsonc` stays as-is.

## Caveats worth repeating

**`--changed` and `--staged` require all three of these to work:**

1. `vcs.enabled: true` in `biome.jsonc`. Biome otherwise has no way to ask git anything — it'll exit with a configuration error.
2. `vcs.defaultBranch` set (or an explicit `--since=<ref>` on the CLI). Without `defaultBranch`, a bare `biome ci --changed` has no idea what "changed vs. base" means. In the Pipelines step above we pass `--since=origin/${BITBUCKET_PR_DESTINATION_BRANCH}` so the config fallback isn't consulted, but local runs will use `defaultBranch`.
3. **A full-depth git clone.** Bitbucket defaults to a shallow clone (depth 50 at time of writing), which often doesn't include the merge-base with the target branch — so `git diff` against `origin/main` produces nonsense or nothing. `clone: { depth: full }` in the step (shown above) fixes this. The equivalent on GitHub Actions is `fetch-depth: 0` on `actions/checkout`.

Also note that `biome ci` refuses `--staged` — use `--changed --since=<base>` in CI and reserve `--staged` for pre-commit.
