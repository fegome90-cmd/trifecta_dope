# Phase 4 Plan — Dependabot PR Merge Order

**Date**: 2026-05-04
**Status**: PLAN ONLY — DO NOT MERGE
**Total PRs**: 10

> ⚠️ Each merge MUST be: individual (one PR at a time), tested after merge, reversible.

## PR Inventory

| # | PR | Package | Version | Branch (confirmed) | Risk | Area | Min Tests After Merge | CI Status |
|---|-----|---------|---------|---------------------|------|------|-----------------------|-----------|
| 1 | #94 | safety | >=2.0.0 → >=3.7.0 | `dependabot/pip/safety-gte-3.7.0` | LOW | security | `uv run pytest -m "not slow"` | Test+Lint FAIL (likely base) |
| 2 | #95 | types-pyyaml | >=6.0 → >=6.0.12.20260408 | `dependabot/pip/types-pyyaml-gte-6.0.12.20260408` | LOW | types | `uv run pytest -m "not slow"` | Test+Lint FAIL (likely base) |
| 3 | #97 | filelock | >=3.20.2 → >=3.25.2 | `dependabot/pip/filelock-gte-3.25.2` | LOW | utility | `uv run pytest -m "not slow"` | Test+Lint FAIL (likely base) |
| 4 | #101 | pytest-env | >=1.2.0 → >=1.6.0 | `dependabot/pip/pytest-env-gte-1.6.0` | LOW | testing | `uv run pytest -m "not slow"` | Test+Lint FAIL (likely base) |
| 5 | #96 | mypy | >=1.19.1 → >=1.20.1 | `dependabot/pip/mypy-gte-1.20.1` | LOW-MEDIUM | types | `uv run pytest -m "not slow" && uv run mypy` | Test+Lint FAIL (likely base) |
| 6 | #100 | plotly | >=5.18.0 → >=6.7.0 | `dependabot/pip/plotly-gte-6.7.0` | MEDIUM | visualization | `uv run pytest -m "not slow"` + visual spot-check | Test+Lint FAIL (likely base) |
| 7 | #99 | ruamel-yaml | >=0.18.0 → >=0.19.1 | `dependabot/pip/ruamel-yaml-gte-0.19.1` | MEDIUM | parsing | `uv run pytest -m "not slow"` + WO system tests | Test+Lint FAIL (likely base) |
| 8 | #98 | tree-sitter | >=0.23.0 → >=0.25.2 | `dependabot/pip/tree-sitter-gte-0.25.2` | MEDIUM | parsing | `uv run pytest -m "not slow"` + AST tests | Test+Lint FAIL (likely base) |
| 9 | #102 | pandas | >=2.0.0 → >=3.0.2 | `dependabot/pip/pandas-gte-3.0.2` | MEDIUM | data | `uv run pytest -m "not slow"` + data pipeline tests | Test+Lint FAIL (likely base) |
| 10 | #93 | typer | >=0.9.0 → >=0.24.1 | `dependabot/pip/typer-gte-0.24.1` | LOW-MEDIUM | CLI | `uv run pytest -m "not slow"` + CLI integration | Test+Lint FAIL (likely base) |

## Recommended Merge Order (Risk-Ascending)

### Wave 1 — Security + Low-Risk (Merge First)

1. **safety >=3.7.0** (#94) — Security update, highest priority. Minor version bump in audit tooling.
2. **types-pyyaml >=6.0.12.20260408** (#95) — Type stubs only, no runtime impact. Patch-level.
3. **filelock >=3.25.2** (#97) — Utility library, minor version. Used for file locking patterns.
4. **pytest-env >=1.6.0** (#101) — Test infrastructure. Only affects test configuration.

### Wave 2 — Type Checker (May Surface New Issues)

5. **mypy >=1.20.1** (#96) — Type checker update. May surface new type errors that were previously silent. Run `uv run mypy` after merge to check.

### Wave 3 — Medium Risk (Test Carefully)

6. **plotly >=6.7.0** (#100) — Major version bump (5→6). API changes possible. Check visualization outputs.
7. **ruamel-yaml >=0.19.1** (#99) — YAML parser used in WO system. Breaking changes in round-trip mode possible.
8. **tree-sitter >=0.25.2** (#98) — Parser dependency. Minor version but AST API surface changes possible.
9. **pandas >=3.0.2** (#102) — Major version bump (2→3). Known breaking changes in pandas 3.0 (deprecated DataFrame.append, etc.).

### Wave 4 — CLI Surface (Leave for Last)

10. **typer >=0.24.1** (#93) — CLI framework. 0.9→0.24 is a significant jump. Touches CLI surface. Highest chance of breaking user-facing commands.

## Notes

### CI Failures
All 10 PRs show failures in "Test Python 3.12" and "Lint and Type Check" CI checks. These are likely **base branch issues** (pre-existing), not caused by the dependabot changes. Verify by checking if main branch CI passes before merging.

### Pandas Branch Confirmation
The pandas branch is `dependabot/pip/pandas-gte-3.0.2` — it targets pandas, NOT pypy. The "pypy" reference in earlier notes was incorrect.

### Merge Protocol (Per PR)
1. `gh pr merge <number> --merge` (or rebase if preferred)
2. `git pull origin main`
3. `uv run pytest -m "not slow"` — minimum smoke test
4. If tests fail: `gh pr revert <number>` and log the failure
5. If tests pass: proceed to next PR

### Pre-Merge Prerequisites
- [ ] Verify main branch CI is green (or at least not worse than current)
- [ ] Ensure local environment is clean (`git status --short` empty)
- [ ] Confirm no active WOs or in-flight work on main

---

*Generated: 2026-05-04 | Status: PLAN ONLY — NO MERGE*
