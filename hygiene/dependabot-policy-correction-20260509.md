# Dependabot Policy — Correction Report

> **Date**: 2026-05-09
> **Type**: Correction report (documentation only — no operational changes)
> **Authority scope**: Documents corrections to `git-hygiene-document-authority-20260509.md` and `dependabot-policy-20260509.md`.
> **Related change**: `git-hygiene-dependabot-policy`

---

## 1. Contradictions Corrected

### 1.1 Authority Registry: "all PRs auto-closed"

**Previous claim** (in `git-hygiene-document-authority-20260509.md` Known Corrections table):

> "All 10 Dependabot PRs (#93-#102) were auto-closed after `dependabot.yml` was deleted."

**Corrected to**:

> PRs #93-#102 had mixed outcomes: 5 MERGED (#94 safety, #97 filelock, #99 ruamel-yaml, #101 pytest-env, #102 pandas), 5 CLOSED (#93 typer, #95 types-pyyaml, #96 mypy, #98 tree-sitter, #100 plotly). `dependabot.yml` was NOT deleted.

**Affected sections**:
- Known Corrections table
- Historical/Superseded table (entry for `dependabot-phase-4-plan-20260504.md`)
- Authority Map by Topic (Dependabot entry)
- Residual Risks #1

### 1.2 Authority Registry: dependabot.yml "must be recreated"

**Previous claim** (Residual Risks #1):

> "`dependabot.yml` must be recreated — Without it, Dependabot will not open new PRs."

**Corrected to**:

> "`dependabot.yml` needs config update — File exists and Dependabot IS active, but current config is overly permissive."

---

## 2. Authority Registry Updates

| Field | Previous | Updated |
|-------|----------|---------|
| Authority Map: Dependabot topic | `dependabot-phase-4-plan-20260504.md` (Resolution section) | `dependabot-policy-20260509.md` (Full document, DRAFT) |
| Historical table: dependabot-phase-4-plan | "All 10 PRs auto-closed, dependabot.yml deleted" | Mixed outcomes (5 merged, 5 closed); dependabot.yml NOT deleted; current authority is `dependabot-policy-20260509.md` |
| Residual Risk #1 | "dependabot.yml must be recreated" | "dependabot.yml needs config update — exists but overly permissive" |

---

## 3. Risk Classification Change

| Package | Previous | Updated | Justification |
|---------|----------|---------|---------------|
| `mypy` | LOW | **MEDIUM** | Although mypy does not touch runtime code, it is the **type gate** for CI. Version changes can introduce new errors that break `mypy src/` on CI, blocking all PRs. This is higher impact than a pure type stub package. |

---

## 4. Additional Semver-Major Ignores Proposed

The conceptual `dependabot.yml` config in `dependabot-policy-20260509.md` was updated to add semver-major ignore rules for:

| Package | Rationale |
|---------|-----------|
| `filelock` | Concurrency behavior; lock semantics could change across majors |
| `jsonschema` | Schema validation core; major API changes could break validation pipelines |
| `tiktoken` | Model-dependent; major version changes affect token counts |
| `pyyaml` / `PyYAML` | YAML parsing core; both naming variants included as Dependabot may use either |

Existing ignores (typer*, tree-sitter*, pandas, pydantic, ruamel.yaml) remain unchanged.

Total ignore entries: 11 (up from 5).

---

## 5. Major Update Policy Section Added

A new Section 4.5 "Major Update Policy" was added to `dependabot-policy-20260509.md` with clear rules per risk tier:

- **HIGH**: ignore semver-major in Dependabot; handle via SDD
- **MEDIUM**: allow only grouped minor/patch; major requires manual review
- **LOW**: may be auto-proposed but never auto-merged
- **SECURITY**: may bypass normal order but still requires CI baseline

---

## 6. Actions Explicitly NOT Taken

1. ❌ `.github/dependabot.yml` NOT modified (operational config unchanged)
2. ❌ No PRs opened
3. ❌ No dependencies updated
4. ❌ No functional code touched
5. ❌ `pyproject.toml` NOT modified
6. ❌ `uv.lock` NOT modified
7. ❌ No branches or tags created/modified
8. ❌ No `--no-verify` used

---

## 7. Confirmation

`.github/dependabot.yml` was **not modified** during this correction. The file exists at HEAD and Dependabot remains active with the existing (pre-correction) configuration.

---

*Generated: 2026-05-09 | Type: Correction report | No operational changes.*
