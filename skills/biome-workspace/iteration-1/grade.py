#!/usr/bin/env python3
"""
Grade each eval's outputs against its assertions.

Writes `grading.json` into each run's directory with fields (text, passed, evidence)
as the eval-viewer expects.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

WORKSPACE = Path(__file__).parent
EVAL_DIRS = sorted(p for p in WORKSPACE.iterdir() if p.is_dir() and p.name.startswith("eval-"))


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_jsonc(path: Path) -> dict | None:
    """Parse a JSON or JSONC file, stripping // and /* */ comments."""
    raw = read(path)
    if not raw:
        return None
    # Strip /* ... */ block comments
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    # Strip // line comments (preserve URLs: only match // not preceded by :)
    raw = re.sub(r"(?m)(^|[^:\"])//[^\n]*", r"\1", raw)
    # Strip trailing commas before } or ]
    raw = re.sub(r",(\s*[}\]])", r"\1", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# -- assertion checkers -------------------------------------------------------


def check_eval0(out_dir: Path) -> list[dict]:
    biome = load_jsonc(out_dir / "biome.jsonc") or {}
    pkg = load_jsonc(out_dir / "package.json.scripts.json") or {}
    response = read(out_dir / "response.md")

    biome_raw = read(out_dir / "biome.jsonc")

    # If scripts file is the wrapping scripts object or just the inner keys, normalize
    scripts = pkg.get("scripts", pkg) if isinstance(pkg, dict) else {}

    results = []

    # 1. schema 2.x
    schema = biome.get("$schema", "")
    results.append({
        "text": "biome.jsonc pins $schema to Biome 2.x",
        "passed": "schemas/2." in schema,
        "evidence": f"$schema = {schema!r}" if schema else "missing $schema",
    })

    # 2. indent 2-space
    fmt = biome.get("formatter", {})
    indent_ok = fmt.get("indentStyle") == "space" and fmt.get("indentWidth") == 2
    results.append({
        "text": "Formatter indent is 2-space",
        "passed": indent_ok,
        "evidence": f"formatter.indentStyle={fmt.get('indentStyle')!r}, indentWidth={fmt.get('indentWidth')!r}",
    })

    # 3. lineWidth 100
    lw = fmt.get("lineWidth")
    results.append({
        "text": "Formatter lineWidth is 100",
        "passed": lw == 100,
        "evidence": f"formatter.lineWidth={lw!r}",
    })

    # 4. js quote/semis/commas
    js = biome.get("javascript", {}).get("formatter", {})
    js_ok = (
        js.get("quoteStyle") == "single"
        and js.get("semicolons") == "asNeeded"
        and js.get("trailingCommas") == "all"
    )
    results.append({
        "text": "JS formatter uses single quotes, no semicolons, trailing commas all",
        "passed": js_ok,
        "evidence": f"quoteStyle={js.get('quoteStyle')!r}, semicolons={js.get('semicolons')!r}, trailingCommas={js.get('trailingCommas')!r}",
    })

    # 5. tailwindDirectives
    tw = biome.get("css", {}).get("parser", {}).get("tailwindDirectives")
    results.append({
        "text": "Tailwind v4 directives enabled (css.parser.tailwindDirectives: true)",
        "passed": tw is True,
        "evidence": f"css.parser.tailwindDirectives={tw!r}",
    })

    # 6. vue override disables noise-prone rules
    overrides = biome.get("overrides", []) or []
    vue_override_found = False
    vue_evidence = "no override matching **/*.vue found"
    for ov in overrides:
        includes = ov.get("includes", []) or ov.get("include", []) or []
        if any("*.vue" in str(i) for i in includes):
            rules = ov.get("linter", {}).get("rules", {})
            style = rules.get("style", {}) or {}
            corr = rules.get("correctness", {}) or {}
            relevant = [
                style.get("useConst"),
                style.get("useImportType"),
                corr.get("noUnusedVariables"),
                corr.get("noUnusedImports"),
            ]
            disabled = [v for v in relevant if v == "off" or (isinstance(v, dict) and v.get("level") == "off")]
            if disabled:
                vue_override_found = True
                vue_evidence = f"vue override disables {len(disabled)} of the 4 target rules"
                break
            else:
                vue_evidence = "vue override found but doesn't disable any of the 4 target rules"
    results.append({
        "text": "Vue files get an override disabling noise-prone rules (useConst/useImportType/noUnused*)",
        "passed": vue_override_found,
        "evidence": vue_evidence,
    })

    # 7. Nuxt build output excluded
    files_incl = biome.get("files", {}).get("includes", []) or []
    files_str = " ".join(str(x) for x in files_incl) if files_incl else biome_raw
    nuxt_excluded = ".nuxt" in files_str and ".output" in files_str
    results.append({
        "text": "Nuxt build output (.nuxt + .output) excluded from files.includes",
        "passed": nuxt_excluded,
        "evidence": f"files.includes has {len(files_incl)} entries; .nuxt present: {'.nuxt' in files_str}; .output present: {'.output' in files_str}",
    })

    # 8. scripts
    needed_script_keys = {"format", "lint", "check", "ci"}
    present = set(scripts.keys()) if isinstance(scripts, dict) else set()
    missing = needed_script_keys - present
    # check commands invoke biome
    biome_invocations = sum(1 for v in (scripts.values() if isinstance(scripts, dict) else []) if "biome" in str(v))
    results.append({
        "text": "package.json scripts include format, lint, check, and ci invoking biome",
        "passed": not missing and biome_invocations >= 4,
        "evidence": f"script keys present: {sorted(present)}; missing from required set: {sorted(missing)}; biome-invoking scripts: {biome_invocations}",
    })

    # 9. Vue experimental call-out
    lc = response.lower()
    vue_mentions_experimental = any(
        kw in lc for kw in ["experimental", "partial", "partially", "2.3", "v2.3", "limited", "experimentally"]
    ) and "vue" in lc
    results.append({
        "text": "Response calls out that Vue support is experimental / partial",
        "passed": vue_mentions_experimental,
        "evidence": f"response.md length={len(response)}; contains 'vue': {'vue' in lc}; contains one of the experimental keywords: {any(kw in lc for kw in ['experimental','partial','partially','2.3','limited'])}",
    })

    return results


def check_eval1(out_dir: Path) -> list[dict]:
    guide = read(out_dir / "migration-guide.md")
    lc = guide.lower()

    results = []

    results.append({
        "text": "Gives exact `biome migrate prettier --write` command",
        "passed": "biome migrate prettier --write" in guide,
        "evidence": "found" if "biome migrate prettier --write" in guide else "NOT found",
    })

    results.append({
        "text": "Gives exact `biome migrate eslint --write` command",
        "passed": "biome migrate eslint --write" in guide,
        "evidence": "found" if "biome migrate eslint --write" in guide else "NOT found",
    })

    del_eslint = "eslint.config.js" in guide or "eslint.config.*" in guide
    del_prettier = ".prettierrc.json" in guide or ".prettierrc" in guide or "prettier.config" in guide
    results.append({
        "text": "Lists old config files to delete (eslint.config.js + .prettierrc.json at minimum)",
        "passed": del_eslint and del_prettier,
        "evidence": f"mentions eslint config file: {del_eslint}; mentions prettierrc: {del_prettier}",
    })

    # uninstall block: mentions pnpm remove / uninstall AND lists eslint + prettier + at least one of the plugins
    mentions_remove_cmd = "pnpm remove" in guide or "pnpm uninstall" in guide or "pnpm -w remove" in guide
    mentions_eslint_core = re.search(r"\beslint\b", guide) is not None
    mentions_prettier_core = re.search(r"\bprettier\b", guide) is not None
    mentions_ts_eslint = "@typescript-eslint" in guide
    mentions_unicorn = "eslint-plugin-unicorn" in guide
    uninstall_ok = mentions_remove_cmd and mentions_eslint_core and mentions_prettier_core and (mentions_ts_eslint or mentions_unicorn)
    results.append({
        "text": "Lists packages to uninstall (eslint + prettier + @typescript-eslint/* or eslint-plugin-unicorn)",
        "passed": uninstall_ok,
        "evidence": f"remove cmd: {mentions_remove_cmd}; eslint: {mentions_eslint_core}; prettier: {mentions_prettier_core}; @typescript-eslint: {mentions_ts_eslint}; unicorn: {mentions_unicorn}",
    })

    scripts_ok = "biome check" in guide and "biome ci" in guide
    results.append({
        "text": "package.json scripts block uses `biome check` and `biome ci`",
        "passed": scripts_ok,
        "evidence": f"'biome check' present: {'biome check' in guide}; 'biome ci' present: {'biome ci' in guide}",
    })

    lint_staged_ok = "lint-staged" in guide and "biome check --write" in guide and "--no-errors-on-unmatched" in guide
    results.append({
        "text": "Updated lint-staged config uses `biome check --write` with `--no-errors-on-unmatched`",
        "passed": lint_staged_ok,
        "evidence": f"lint-staged: {'lint-staged' in guide}; biome check --write: {'biome check --write' in guide}; --no-errors-on-unmatched: {'--no-errors-on-unmatched' in guide}",
    })

    # Biome default indent is tab (gotcha)
    tab_gotcha = (
        ("tab" in lc and ("default" in lc or "biome defaults" in lc))
        or "indentstyle: \"space\"" in lc
        or "indentstyle: 'space'" in lc
        or "match prettier" in lc and "tab" in lc
    )
    results.append({
        "text": "Gotchas section mentions Biome's default indent is tab",
        "passed": tab_gotcha,
        "evidence": f"'tab' in text: {'tab' in lc}; 'default' in text: {'default' in lc}",
    })

    # recommended:true gets disabled
    rec_gotcha = (
        "recommended: false" in guide
        or "recommended:false" in guide
        or ("recommended" in lc and "disable" in lc)
        or ("recommended" in lc and "replaces" in lc)
        or ("recommended" in lc and "overwrites" in lc)
        or ("recommended" in lc and "explicit" in lc and "list" in lc)
    )
    results.append({
        "text": "Gotchas section mentions `migrate eslint` disables recommended:true or replaces it",
        "passed": rec_gotcha,
        "evidence": f"'recommended' mentioned: {'recommended' in lc}; coupled with disable/replaces/overwrites/explicit-list keywords",
    })

    yaml_gotcha = "yaml" in lc and ("not support" in lc or "doesn't support" in lc or "isn't support" in lc or "convert" in lc)
    results.append({
        "text": "Mentions ESLint YAML configs are not supported by migrate",
        "passed": yaml_gotcha,
        "evidence": f"'yaml' in text: {'yaml' in lc}; with support-negation or convert keyword",
    })

    naming_gotcha = (
        "camelcase" in lc and "kebab" in lc
    ) or "camelCase" in guide and "kebab-case" in guide
    results.append({
        "text": "Mentions ESLint kebab-case vs Biome camelCase rule names",
        "passed": naming_gotcha,
        "evidence": f"'camelCase' present: {'camelCase' in guide or 'camelcase' in lc}; 'kebab-case' present: {'kebab-case' in guide or 'kebab' in lc}",
    })

    return results


def check_eval2(out_dir: Path) -> list[dict]:
    lefthook = read(out_dir / "lefthook.yml")
    pipelines = read(out_dir / "bitbucket-pipelines.yml")
    patch = load_jsonc(out_dir / "biome-config-patch.jsonc") or {}
    response = read(out_dir / "response.md")
    response_lc = response.lower()

    results = []

    results.append({
        "text": "lefthook.yml uses `stage_fixed: true`",
        "passed": "stage_fixed: true" in lefthook,
        "evidence": "present" if "stage_fixed: true" in lefthook else "missing",
    })

    hook_ok = (
        "biome check" in lefthook
        and "--write" in lefthook
        and "--no-errors-on-unmatched" in lefthook
        and "--files-ignore-unknown" in lefthook
    )
    results.append({
        "text": "lefthook runs `biome check --write --no-errors-on-unmatched --files-ignore-unknown`",
        "passed": hook_ok,
        "evidence": f"has check:{'biome check' in lefthook}; --write:{'--write' in lefthook}; --no-errors-on-unmatched:{'--no-errors-on-unmatched' in lefthook}; --files-ignore-unknown:{'--files-ignore-unknown' in lefthook}",
    })

    results.append({
        "text": "lefthook passes {staged_files} to biome",
        "passed": "{staged_files}" in lefthook,
        "evidence": "present" if "{staged_files}" in lefthook else "missing",
    })

    uses_ci = "biome ci" in pipelines
    results.append({
        "text": "bitbucket-pipelines.yml uses `biome ci` (not `biome check`)",
        "passed": uses_ci,
        "evidence": f"'biome ci' present: {uses_ci}",
    })

    results.append({
        "text": "bitbucket-pipelines.yml scopes to changed files with --changed",
        "passed": "--changed" in pipelines,
        "evidence": "present" if "--changed" in pipelines else "missing",
    })

    junit_ok = "--reporter=junit" in pipelines and (".xml" in pipelines or "junit" in pipelines)
    results.append({
        "text": "bitbucket-pipelines.yml emits a JUnit report",
        "passed": junit_ok,
        "evidence": f"--reporter=junit present: {'--reporter=junit' in pipelines}; xml artifact path mentioned: {'.xml' in pipelines}",
    })

    artifact_ok = "artifacts:" in pipelines or "test-results" in pipelines or "test-reports" in pipelines
    results.append({
        "text": "JUnit file exposed as a Pipelines artifact (or via test-reports/)",
        "passed": artifact_ok,
        "evidence": f"'artifacts:' present: {'artifacts:' in pipelines}; 'test-reports' present: {'test-reports' in pipelines}; 'test-results' present: {'test-results' in pipelines}",
    })

    vcs = patch.get("vcs", {}) if isinstance(patch, dict) else {}
    vcs_ok = vcs.get("enabled") is True and bool(vcs.get("defaultBranch"))
    results.append({
        "text": "biome-config-patch enables vcs.enabled:true with defaultBranch set",
        "passed": vcs_ok,
        "evidence": f"vcs.enabled={vcs.get('enabled')!r}, vcs.defaultBranch={vcs.get('defaultBranch')!r}",
    })

    depth_ok = (
        "fetch-depth" in response_lc
        or "fetch depth" in response_lc
        or "clone.depth" in response_lc
        or "shallow clone" in response_lc
        or "shallow" in response_lc
        or "full clone" in response_lc
        or "deep clone" in response_lc
        or "depth: full" in response_lc
    )
    results.append({
        "text": "Response warns about needing full git history / deep clone for --changed",
        "passed": depth_ok,
        "evidence": f"response mentions clone depth / shallow keyword: {depth_ok}",
    })

    return results


CHECKERS = {
    "eval-0-fresh-setup-nuxt-pnpm": check_eval0,
    "eval-1-migrate-eslint-prettier": check_eval1,
    "eval-2-ci-and-precommit-bitbucket": check_eval2,
}


def main():
    overall = {}
    for eval_dir in EVAL_DIRS:
        checker = CHECKERS.get(eval_dir.name)
        if not checker:
            continue
        for variant in ("with_skill", "without_skill"):
            out_dir = eval_dir / variant / "outputs"
            if not out_dir.exists():
                continue
            results = checker(out_dir)
            grading_path = eval_dir / variant / "grading.json"
            grading_path.write_text(json.dumps({"expectations": results}, indent=2))
            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            overall.setdefault(eval_dir.name, {})[variant] = (passed, total)
            print(f"{eval_dir.name} [{variant}]: {passed}/{total}")

    print("\n=== Summary ===")
    for name, variants in overall.items():
        line = f"{name}: "
        for v, (p, t) in variants.items():
            line += f"{v}={p}/{t}  "
        print(line)


if __name__ == "__main__":
    main()
