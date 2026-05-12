# Dependabot Policy — SemVer 0.x Correction Report

> **Date**: 2026-05-09
> **Type**: Correction report (documentation only — no operational changes)
> **Authority scope**: Documents semver 0.x risk correction to `dependabot-policy-20260509.md`.
> **Related change**: `git-hygiene-dependabot-policy`
> **Precedes**: Operational apply of `.github/dependabot.yml`

---

## 1. Problem Detected

The dependabot policy draft only blocked `semver-major` updates for HIGH packages. However, several critical packages are at version `0.x`, where SemVer explicitly states that **minor bumps may be breaking** ([semver.org §4](https://semver.org/#spec-item-4)):

> "Major version zero (0.y.z) is for initial development. Anything MAY change at any time."

This means `typer 0.9 → 0.24` (a "semver-minor" jump of 15 versions) would be allowed through by the proposed config, despite being exactly the type of update the policy was designed to control.

## 2. Affected Packages

| Package | Current Floor | 0.x Risk | Why Minor Can Break |
|---------|---------------|----------|---------------------|
| `typer*` | >=0.9.0 | ✅ Yes | CLI surface changes; touches every command |
| `tree-sitter*` | >=0.25.2 | ✅ Yes | AST API surface changes across minors |
| `ruamel.yaml` | >=0.19.1 | ✅ Yes | Round-trip behavior; used in WO system |
| `tiktoken` | >=0.12.0 | ✅ Yes | Model-dependent tokenization; counts can shift |

## 3. Changes Made

### 3.1 Semver-minor ignores added to YAML conceptual config

For the 4 HIGH 0.x packages above, `version-update:semver-minor` was added alongside the existing `version-update:semver-major` in the `ignore` rules.

Non-0.x HIGH packages (pandas, pydantic, filelock, jsonschema, pyyaml) retain semver-major-only ignores — their stable major versions provide backward-compatible minor bumps.

### 3.2 Major Update Policy corrected (Section 4.5)

Replaced simple "ignore semver-major" with explicit tier handling:
- **HIGH**: patch-only by Dependabot. Semver-major AND 0.x semver-minor → ignored, SDD required.
- **MEDIUM**: grouped minor/patch only. Semver-major → manual review required.
- **LOW**: may be proposed, never auto-merged.
- **SECURITY**: priority lane, CI baseline still required.

### 3.3 Section 4.6 "0.x SemVer Risk" added

New section explaining the 0.x risk with concrete typer example and policy implications.

### 3.4 `prod-cli` group added

Added `prod-cli` group to both the grouping table and YAML conceptual config:
```yaml
prod-cli:
  patterns:
    - "typer*"
  update-types:
    - "patch"
```

### 3.5 Grouping table and YAML synced

The grouping table in Section 5.3 now matches exactly the `groups:` section in the YAML conceptual config. Both include: `dev-test-deps`, `dev-lint-type`, `prod-core`, `prod-parser`, `prod-cli`.

### 3.6 Residual risk added

Added "0.x SemVer risk for CLI/parser/tokenization packages" to the residual risks table (Section 8).

## 4. Confirmation

- ❌ `.github/dependabot.yml` was **NOT modified**. Operational config unchanged.
- ✅ Document remains **DRAFT** — still awaiting human review.
- ✅ Grouping table and YAML conceptual config are **exactly consistent**.
- ✅ The proposed config would **NOT** allow `typer 0.9 → 0.24` as an automatic Dependabot update.

## 5. Actions Explicitly NOT Taken

1. ❌ `.github/dependabot.yml` NOT modified
2. ❌ No PRs opened
3. ❌ No dependencies updated
4. ❌ No functional code touched
5. ❌ `pyproject.toml` NOT modified
6. ❌ `uv.lock` NOT modified
7. ❌ No branches or tags created/modified
8. ❌ No `--no-verify` used

---

*Generated: 2026-05-09 | Type: SemVer correction report | Status: DRAFT | No operational changes.*
