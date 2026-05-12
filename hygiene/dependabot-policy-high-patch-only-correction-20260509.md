# Dependabot Policy — HIGH Patch-Only Consistency Correction

> **Date**: 2026-05-09
> **Status**: CORRECTION REPORT
> **Corrects**: `dependabot-policy-20260509.md` — Section 4.5, Section 4.6, Section 5.4, YAML conceptual, Key Changes table, risk table
> **Authority**: See `git-hygiene-document-authority-20260509.md`

---

## Contradiction Detected

The policy document declared "HIGH packages = patch-only by Dependabot" (Section 4.5), but the YAML conceptual config only ignored `semver-major` for HIGH stable packages (pandas, pydantic, filelock, jsonschema, pyyaml/PyYAML). This meant Dependabot could still auto-propose `semver-minor` upgrades for these packages — contradicting the patch-only policy.

The 0.x HIGH packages (typer*, tree-sitter*, ruamel.yaml, tiktoken) already had both `semver-major` + `semver-minor` ignored. The gap was limited to stable-major HIGH packages.

## Changes Applied

### 1. Section 4.5 — Added stable semver-minor policy line

Added explicit rule: "HIGH stable semver-minor: **ignored**, SDD required."

### 2. Section 4.6 — Corrected non-0.x HIGH statement

Changed from: "Non-0.x HIGH packages follow standard semver-major-only ignores, as their stable major version provides backward-compatible minor bumps."

Changed to: "Non-0.x HIGH packages ALSO ignore semver-minor — these are patch-only by Dependabot. Minor/major upgrades require SDD/manual review."

### 3. Section 5.4 — Corrected major update rule

Replaced: "Dependabot opens major updates as INDIVIDUAL PRs (not grouped)"

With: "Dependabot must not auto-propose HIGH major upgrades. HIGH upgrades beyond patch are handled through SDD/manual review. Non-HIGH major upgrades may appear as individual PRs only if not explicitly ignored, and still require manual review."

Updated all ignore rules bullets for stable HIGH packages to show `semver-major + semver-minor` with "patch-only by Dependabot" rationale.

### 4. YAML conceptual — Added semver-minor ignores for stable HIGH packages

Added `version-update:semver-minor` to:
- `pandas`
- `pydantic`
- `filelock`
- `jsonschema`
- `pyyaml`
- `PyYAML`

Updated YAML comment from "HIGH stable-major packages: semver-major only (0.x semver-minor is safe)" to "HIGH packages: Dependabot patch-only. Minor/major require SDD/manual review."

### 5. Key Changes table — Updated ignore rules description

Updated to: "11 entries — ALL HIGH packages ignore semver-major + semver-minor. HIGH = patch-only by Dependabot."

### 6. Risk table — Updated filelock/tiktoken risk

Changed from: "No dependabot groups for filelock/tiktoken — These fall outside current groups; will be individual PRs"

Changed to: "filelock/tiktoken not in dependabot groups — Both controlled by ignore rules (semver-major + semver-minor); Dependabot will only propose patch updates. Minor/major still require manual SDD review."

## Complete List of HIGH Packages Now Patch-Only by Dependabot

| Package | semver-major ignored | semver-minor ignored | Rationale |
|---------|---------------------|---------------------|-----------|
| `typer*` | Yes | Yes | 0.x: CLI surface, minors can be breaking |
| `tree-sitter*` | Yes | Yes | 0.x: AST API can change across minors |
| `ruamel.yaml` | Yes | Yes | 0.x: round-trip behavior can change |
| `tiktoken` | Yes | Yes | 0.x: token counts can shift |
| `pandas` | Yes | **Yes** (added) | Data stack: deprecated APIs across minors |
| `pydantic` | Yes | **Yes** (added) | Data validation: breaking changes possible across minors |
| `filelock` | Yes | **Yes** (added) | Concurrency: lock semantics can change |
| `jsonschema` | Yes | **Yes** (added) | Schema validation: pipeline can break |
| `pyyaml` / `PyYAML` | Yes | **Yes** (added) | YAML parsing core |

## Confirmation

- `.github/dependabot.yml` was **NOT modified**. Only the conceptual YAML in the policy document was updated.
- The policy document remains **DRAFT** until human review and approval.
- No operational changes were made.
- No functional code was touched.
- No branches or tags were created/modified.

---

*Generated: 2026-05-09 | Status: CORRECTION REPORT | Corrects: dependabot-policy-20260509.md | No operational changes.*
