# Biome in CI + pre-commit (Bitbucket, lefthook)

Three files, wired together so that local commits auto-fix and CI stays read-only and fast.

## 1. Pre-commit hook (`lefthook.yml`)

```yaml
pre-commit:
  parallel: true
  commands:
    biome:
      glob: "*.{js,jsx,ts,tsx,mjs,cjs,mts,cts,json,jsonc,css}"
      run: npx biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true
```

Why this shape:

- `biome check --write` runs the formatter, safe lint fixes, and safe import organization in one pass. Unsafe fixes are intentionally left off so commits never get surprise semantic rewrites — devs can opt into `--unsafe` manually.
- `{staged_files}` is lefthook's built-in templating for "only the paths staged for this commit". Combined with `glob`, Biome is only invoked on relevant staged files.
- `stage_fixed: true` is the lefthook-native equivalent of husky+lint-staged's re-add step: anything Biome rewrote gets `git add`-ed back into the index so the commit includes the fix.
- `--no-errors-on-unmatched` and `--files-ignore-unknown=true` keep the hook quiet when staged files are e.g. all markdown or all images.

Install lefthook and its git hooks once per clone:

```bash
npm install --save-dev lefthook
npx lefthook install
```

## 2. Bitbucket Pipelines (`bitbucket-pipelines.yml`)

```yaml
image: node:20

definitions:
  caches:
    npm: ~/.npm

pipelines:
  pull-requests:
    '**':
      - step:
          name: Biome (changed files vs target)
          caches:
            - npm
            - node
          script:
            - export TARGET="${BITBUCKET_PR_DESTINATION_BRANCH}"
            - git fetch --no-tags --depth=50 origin "+refs/heads/${TARGET}:refs/remotes/origin/${TARGET}"
            - npm ci
            - mkdir -p test-results
            - npx biome ci
                --changed
                --since="origin/${TARGET}"
                --reporter=junit
                --no-errors-on-unmatched
                > test-results/biome-junit.xml
          artifacts:
            - test-results/**
```

Why this shape:

- The `pull-requests:` trigger only fires on PRs, which is what you asked for.
- `biome ci` is Biome's dedicated read-only CI entry point — it never writes and exits non-zero on any formatter/lint/assist diagnostic.
- `--changed --since=origin/$TARGET` restricts the check to files that differ from the PR's target branch. `BITBUCKET_PR_DESTINATION_BRANCH` is set automatically for PR pipelines.
- Bitbucket's default clone is shallow and won't contain the target branch, so we explicitly `git fetch` it (depth 50 is enough for normal PRs; bump if your branches diverge further). Without this fetch, `--since=origin/main` will error with "unknown revision".
- `--reporter=junit` writes JUnit XML to stdout; Bitbucket Pipelines auto-discovers any `**/test-results/*.xml` file and surfaces it on the pipeline's **Tests** tab. No extra plugin or step needed. We also persist it as an artifact so you can download the raw XML.

## 3. `biome.jsonc` patch

`--changed` requires Biome's VCS integration to be enabled — otherwise Biome has no idea what "changed" means. Merge these keys into your existing config:

```jsonc
{
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "defaultBranch": "main",
    "useIgnoreFile": true
  }
}
```

- `enabled: true` is the switch that makes `--changed` / `--since` work at all.
- `clientKind: "git"` is currently the only supported value, but it's required.
- `defaultBranch: "main"` is a fallback used when `--since` isn't passed. Our CI always passes `--since=origin/$TARGET` explicitly, so this only matters if you also run `biome ci --changed` locally.
- `useIgnoreFile: true` makes Biome respect `.gitignore`, which you almost always want.

No other config changes are required.

## How the pieces fit

- **Locally:** `git commit` -> lefthook runs `biome check --write` on staged files -> fixes get re-staged -> commit proceeds. Devs never have to think about formatting.
- **On PR:** Bitbucket opens a pipeline -> fetches target branch -> `biome ci --changed --since=origin/$TARGET` checks only the diff -> JUnit XML lands in `test-results/` -> Bitbucket renders each diagnostic as a failed test in the Tests tab, with file + line.
- **Scaling:** CI time is O(PR size), not O(repo size). A one-file PR takes seconds even in a 10k-file repo.

## Gotchas worth knowing

- If a contributor skips the hook (`git commit --no-verify`), CI will still catch them — that's the point of having both layers.
- If your default branch isn't `main`, update `defaultBranch` in `biome.jsonc`. The CI snippet already uses `BITBUCKET_PR_DESTINATION_BRANCH`, so it doesn't care.
- If PRs sometimes diverge by more than 50 commits from target (long-lived feature branches), bump `--depth=50` in the fetch. Alternatively, set the repository-level **Clone depth** in Bitbucket repository settings.
- Bitbucket's JUnit discovery is path-based. Don't rename `test-results/` without also updating where you look for the artifact.
