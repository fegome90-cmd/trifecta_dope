# Dependabot Policy — 2026-05-09

> **Status**: DRAFT — Awaiting human review.
> **Change**: `git-hygiene-dependabot-policy`
> **Authority scope**: Follow-up #3 from git hygiene cycle (engram #2748).
> **Constraints**: No dependabot.yml recreation, no PRs opened, no dependencies updated, no functional code touched.

---

## 1. Veredicto Preliminar

`dependabot.yml` **still exists** in the repo at HEAD. The Phase 4 documentation (`dependabot-phase-4-plan-20260504.md`) claimed it was deleted and PRs auto-closed, but this is **partially inaccurate**: the file exists and 5 of 10 PRs were actually **MERGED**. Only 5 were closed. The existing `dependabot.yml` has issues (high `open-pull-requests-limit: 10`, aggressive grouping, no ignore rules for major bumps), but Dependabot IS currently active.

**Verdict**: Policy must be drafted to *improve* the existing configuration, not recreate it from scratch. The current config is overly permissive and generates noisy PR queues.

---

## 2. Estado Actual

### 2.1 dependabot.yml

**EXISTS** at `.github/dependabot.yml`. Current configuration:

| Setting | Value | Assessment |
|---------|-------|------------|
| Ecosystem | `pip` + `github-actions` | Correct |
| Schedule | Weekly, Monday 09:00 | Acceptable |
| `open-pull-requests-limit` | 10 (pip), 5 (actions) | **TOO HIGH** — caused noisy queue |
| Reviewers | `fegome90-cmd` | Correct |
| Labels | `dependencies`, `python` / `github-actions` | OK |
| Groups | `dev-dependencies` (pytest*/ruff/mypy/pyright), `production-dependencies` (typer*/pydantic/pyyaml/tree-sitter*) | **Incomplete** — missing ruamel.yaml, filelock, jsonschema, tiktoken |
| Allow | `dependency-type: "all"` | Acceptable |
| Commit prefix | `chore(deps)` | OK |

### 2.2 Dependency Inventory (from pyproject.toml)

**Runtime dependencies** (production):
| Package | Floor | Purpose |
|---------|-------|---------|
| `typer[all]` | >=0.9.0 | CLI framework |
| `pydantic` | >=2.0 | Data validation |
| `pyyaml` | >=6.0 | YAML parsing (std) |
| `ruamel.yaml` | >=0.19.1 | YAML parsing (round-trip) |
| `tree-sitter` | >=0.25.2 | AST parsing |
| `tree-sitter-python` | >=0.25.0 | Python grammar for tree-sitter |
| `jsonschema` | >=4.0.0 | Schema validation |
| `filelock` | >=3.25.2 | File locking |
| `tiktoken` | >=0.12.0 | Tokenization |

**Dev dependencies** (optional-dependencies.dev):
| Package | Floor | Purpose |
|---------|-------|---------|
| `pytest` | >=7.0 | Test runner |
| `pytest-cov` | latest | Coverage reporting |
| `ruff` | latest | Linter/formatter |
| `pyrefly` | latest | Type checker |
| `pyright` | ==1.1.408 | Type checker (pinned) |
| `bandit[toml]` | >=1.7.0 | Security scanner |
| `safety` | >=3.7.0 | Vulnerability scanner |
| `types-PyYAML` | >=6.0.12.20260408 | Type stubs |
| `jupyter` | >=1.0.0 | Notebook environment |
| `pandas` | >=3.0.2 | Data analysis |
| `kaleido` | >=0.2.0 | Static image export |

**Dependency groups** (tool.dependency-groups.dev):
| Package | Floor | Purpose |
|---------|-------|---------|
| `mypy` | >=1.19.1 | Type checker |
| `pytest-env` | >=1.6.0 | Test env configuration |

**Telemetry optional group**:
| Package | Floor | Purpose |
|---------|-------|---------|
| `jupyter` | >=1.0.0 | Notebook environment |
| `pandas` | >=3.0.2 | Data analysis |
| `kaleido` | >=0.2.0 | Static image export |

### 2.3 uv.lock Stats

- **Total lines**: 2,765
- **Format**: uv lockfile v1, revision 3
- **Python**: >=3.12
- **Resolution markers**: 6 (cross-platform, Python <3.14 and >=3.14)

### 2.4 CI Workflows Related to Dependencies

| Workflow | Relevant Steps |
|----------|---------------|
| `ci.yml` | `uv sync --all-extras` → `pytest` → `ruff check` → `ruff format --check` → `mypy src/` |
| `security-scan.yml` | `bandit -r src/` → `safety check --json` |
| `wo-weekly-gate.yml` | `uv sync --all-extras` → WO health check |

---

## 3. Historial de PRs Auto-cerrados / Mergeados

**Correction to Phase 4 documentation**: Not all 10 PRs were auto-closed. 5 were MERGED.

| PR | Package | Version Change | Actual State | Resolution |
|-----|---------|---------------|--------------|------------|
| #94 | safety | >=2.0.0 → >=3.7.0 | **MERGED** | Merged to main |
| #95 | types-pyyaml | >=6.0 → >=6.0.12.20260408 | CLOSED | Type stubs; not critical |
| #96 | mypy | >=1.19.1 → >=1.20.1 | CLOSED | **Still needed** — floor update pending |
| #97 | filelock | >=3.20.2 → >=3.25.2 | **MERGED** | Merged to main |
| #98 | tree-sitter | >=0.23.0 → >=0.25.2 | CLOSED | Floor already updated manually in Phase 5 |
| #99 | ruamel-yaml | >=0.18.0 → >=0.19.1 | **MERGED** | Merged to main |
| #100 | plotly | >=5.18.0 → >=6.7.0 | CLOSED | Ghost dep — removed entirely in Phase 5 |
| #101 | pytest-env | >=1.2.0 → >=1.6.0 | **MERGED** | Merged to main |
| #102 | pandas | >=2.0.0 → >=3.0.2 | **MERGED** | Merged to main |
| #93 | typer | >=0.9.0 → >=0.24.1 | CLOSED | **Still needed** — major version jump, CLI surface |

### Additional Historical Dependabot PRs

| PR | Package | State |
|----|---------|-------|
| #82 | codecov/codecov-action 5→6 | CLOSED |
| #67 | actions/upload-artifact 6→7 | CLOSED |
| #65 | actions/upload-artifact 4→6 | MERGED |
| #49 | actions/upload-artifact 4→6 | MERGED |
| #21 | pyright 1.1.407→1.1.408 | MERGED |
| #16 | astral-sh/setup-uv 4→7 | CLOSED |
| #15 | pyright 1.1.390→1.1.407 | MERGED |
| #14 | github/codeql-action 3→4 | MERGED |
| #13 | actions/setup-python 5→6 | MERGED |
| #12 | actions/checkout 4→6 | MERGED |

**Total**: 20 Dependabot PRs in repo history. 12 merged, 8 closed.

---

## 4. Dependencias por Categoría / Riesgo

### LOW — Type stubs / no runtime impact

| Package | Category | Rationale |
|---------|----------|-----------|
| `types-PyYAML` | Type stubs | No runtime code; only affects mypy/pyright |
| `mypy` | Type checker (dev) | Static analysis tool; CI failures are caught before merge |

### MEDIUM — Tooling / test / dev dependencies

| Package | Category | Rationale |
|---------|----------|-----------|
| `pytest` | Test runner | Breaking changes rare but possible in majors |
| `pytest-cov` | Coverage | Usually follows pytest versions |
| `pytest-env` | Test config | Low risk; configuration-only |
| `ruff` | Linter/formatter | Fast-moving; breaking rules possible |
| `pyrefly` | Type checker | New tool; rapid iteration |
| `pyright` | Type checker (pinned) | **Pinned to ==1.1.408** — do NOT auto-update |
| `bandit[toml]` | Security scanner | Dev-only; rule changes possible |
| `safety` | Vulnerability scanner | Dev-only; DB format changes possible |
| `jupyter` | Notebook | Dev/telemetry only; large dependency tree |
| `kaleido` | Image export | Dev/telemetry only; minor risk |

### HIGH — CLI surface / parser / AST / YAML / lock behavior

| Package | Category | Rationale |
|---------|----------|-----------|
| `typer[all]` | CLI framework | **0.9→0.24 is a massive jump**; touches every CLI command |
| `ruamel.yaml` | YAML parser (round-trip) | Used in WO system; round-trip behavior can break |
| `tree-sitter` | AST parser | API surface changes across minors |
| `tree-sitter-python` | Grammar | Must stay compatible with tree-sitter version |
| `filelock` | File locking | Concurrency behavior; lock semantics |
| `pandas` | Data stack | Major 2→3 jump; deprecated APIs (DataFrame.append, etc.) |
| `pydantic` | Data validation | Major breaking changes between v2 minors |
| `tiktoken` | Tokenization | Model-dependent; version changes affect token counts |

### SECURITY — Prioritize by vulnerability

| Package | Notes |
|---------|-------|
| `safety` | Scanner itself — run `safety check` before trusting |
| `bandit[toml]` | Scanner itself — update for new detection rules |
| Any dep with CVE | Auto-prioritize; security updates bypass queue limits |

---

## 5. Política Propuesta

### 5.1 Frequency

- **Schedule**: Weekly, Monday 09:00 UTC (keep current)
- **Rationale**: Weekly catches security patches fast enough without daily noise

### 5.2 Queue Limits

- **`open-pull-requests-limit`**: **3** for pip, **2** for github-actions
- **Rationale**: Previous limit of 10 created an unmanageable queue. 3 keeps the pipeline flowing without drowning reviewers.

### 5.3 Grouping Strategy

| Group | Patterns | Update Types | Rationale |
|-------|----------|-------------|-----------|
| `dev-test-deps` | `pytest*`, `pytest-env`, `pytest-cov` | minor, patch | Test infra; low cross-risk |
| `dev-lint-type` | `ruff`, `mypy`, `pyrefly`, `types-*` | minor, patch | Static analysis; low runtime risk |
| `prod-core` | `pydantic`, `pyyaml`, `ruamel.yaml`, `jsonschema` | patch only | Core data layer; group patches |
| `prod-parser` | `tree-sitter*` | patch only | AST stability critical |
| `prod-cli` | `typer*` | patch only | CLI surface; never auto-major |

### 5.4 Major Updates

- **Rule**: Dependabot opens major updates as INDIVIDUAL PRs (not grouped)
- **Action**: Major updates require manual review + targeted testing
- **Ignore rules**:
  - `typer` major (0.x → 1.x or beyond): manual decision required
  - `pandas` major: requires telemetry group validation
  - `tree-sitter` major: requires AST test suite validation
  - `pydantic` major: requires full model validation

### 5.5 Security Updates

- **Rule**: Security updates bypass `open-pull-requests-limit`
- **Action**: Security PRs get `security` label; merge within 48 hours if CI passes
- **Validation**: `safety check` + `bandit -r src/` must pass on CI

### 5.6 No Auto-Merge

- **Rule**: NEVER enable auto-merge on Dependabot PRs
- **Rationale**: Every update touches the lockfile; must be human-reviewed

### 5.7 Merge Requirements

Before merging ANY Dependabot PR:

1. CI passes (test + lint + typecheck)
2. `uv sync` succeeds on clean checkout
3. Smoke tests: `uv run pytest tests/unit -v`
4. Package-specific tests (see Section 6)
5. No regression vs main baseline

### 5.8 When to Close vs Fix

- **Close**: If PR conflicts with newer floor already in pyproject.toml
- **Close**: If package was removed from pyproject.toml (ghost dep)
- **Close + Recreate**: If branch is stale >30 days and rebase fails
- **Fix**: If CI failure is in the PR's own code (not pre-existing)
- **Never force-merge**: If CI fails, close and recreate later

---

## 6. dependabot.yml Conceptual (NO crear archivo)

```yaml
# Dependabot configuration — PROPOSED (not yet applied)
# This is a conceptual config for review. Do NOT create this file yet.
version: 2
updates:
  # Python dependencies (pip/uv via pyproject.toml)
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 3  # REDUCED from 10 to prevent noisy queue
    reviewers:
      - "fegome90-cmd"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
    allow:
      - dependency-type: "all"
    # Ignore major updates for high-risk packages (require manual decision)
    ignore:
      - dependency-name: "typer*"
        update-types: ["version-update:semver-major"]
      - dependency-name: "tree-sitter*"
        update-types: ["version-update:semver-major"]
      - dependency-name: "pandas"
        update-types: ["version-update:semver-major"]
      - dependency-name: "pydantic"
        update-types: ["version-update:semver-major"]
      - dependency-name: "ruamel.yaml"
        update-types: ["version-update:semver-major"]
    groups:
      dev-test-deps:
        patterns:
          - "pytest*"
          - "pytest-env"
          - "pytest-cov"
        update-types:
          - "minor"
          - "patch"
      dev-lint-type:
        patterns:
          - "ruff"
          - "mypy"
          - "pyrefly"
          - "types-*"
        update-types:
          - "minor"
          - "patch"
      prod-core:
        patterns:
          - "pydantic"
          - "pyyaml"
          - "ruamel.yaml"
          - "jsonschema"
        update-types:
          - "patch"
      prod-parser:
        patterns:
          - "tree-sitter*"
        update-types:
          - "patch"

  # GitHub Actions dependencies
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 2  # REDUCED from 5
    reviewers:
      - "fegome90-cmd"
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "chore(ci)"
```

### Key Changes from Current Config

| Setting | Current | Proposed | Reason |
|---------|---------|----------|--------|
| `open-pull-requests-limit` (pip) | 10 | **3** | Prevent noisy queue |
| `open-pull-requests-limit` (actions) | 5 | **2** | Actions rarely need updates |
| `ignore` rules | None | **5 packages** | Block auto-major for HIGH risk |
| Groups: `prod-core` | Missing | **Added** | Group pydantic/pyyaml/ruamel/jsonschema patches |
| Groups: `prod-parser` | Missing | **Added** | Group tree-sitter patches |
| Groups: `dev-test-deps` | Missing (only `dev-dependencies`) | **Replaced** | More specific grouping |
| Groups: `dev-lint-type` | Missing | **Added** | Separate linting from testing |
| Groups: `production-dependencies` | Broad (typer/pydantic/pyyaml/tree-sitter) | **Removed** | Too broad; split into prod-core + prod-parser |
| `timezone` | Not set | **UTC** | Explicit is better |

---

## 7. Merge Protocol for Future Dependabot PRs

### 7.1 Pre-merge Baseline

```bash
# 1. Ensure main is clean
git checkout main && git pull origin main

# 2. Run baseline CI
uv sync --all-extras
uv run pytest tests/unit -v          # Unit baseline
uv run pytest tests/integration -v   # Integration baseline
uv run ruff check src/ tests/        # Lint baseline
uv run mypy src/                      # Type baseline
```

### 7.2 Per-PR Validation

```bash
# 1. Checkout PR
gh pr checkout <number>

# 2. Sync dependencies
uv sync --all-extras

# 3. Smoke tests
uv run pytest tests/unit -v

# 4. Package-specific tests (by category)
# LOW (types/stubs): no extra tests needed
# MEDIUM (test/lint tools): uv run pytest tests/ -v
# HIGH (parser/CLI): run targeted test suites
#   - typer:        uv run pytest tests/integration/cli/ -v
#   - tree-sitter:  uv run pytest tests/unit/test_segment_parser*.py -v
#   - ruamel.yaml:  uv run pytest tests/ -k "wo" -v
#   - pandas:       uv run pytest tests/ -k "telemetry" -v
# SECURITY:        uv run safety check && uv run bandit -r src/ -ll
```

### 7.3 Merge Decision

- ✅ Merge if: CI passes + package-specific tests pass + no baseline regression
- ❌ Close if: CI fails AND failure is caused by PR (not pre-existing)
- ❌ Close if: Package no longer in pyproject.toml
- 🔄 Rebase if: Conflicts but PR is still relevant

### 7.4 Post-merge Verification

```bash
git checkout main && git pull origin main
uv sync --all-extras
uv run pytest tests/unit -v
```

### 7.5 Revert Protocol

If post-merge regression is detected:

```bash
# 1. Revert the merge
git revert -m 1 HEAD

# 2. Document the failure
# Add entry to _ctx/session_trifecta_dope.md

# 3. Close the Dependabot PR if still open
gh pr close <number> --comment "Reverted due to regression: <description>"
```

---

## 8. Riesgos Residuales

| Risk | Severity | Mitigation |
|------|----------|------------|
| **mypy floor not updated** | MEDIUM | PR #96 was closed; mypy >=1.20.1 update needs separate SDD cycle |
| **typer major version gap** | HIGH | typer floor is >=0.9.0 but latest is 0.24.x; major jump deferred but will grow |
| **types-pyyaml update missed** | LOW | PR #95 was closed; stubs don't affect runtime but type coverage is stale |
| **dependabot.yml still has old config** | MEDIUM | Active but permissive; needs replacement with proposed config |
| **pyright pinned to ==1.1.408** | LOW | Intentional pin; may need periodic manual updates |
| **No dependabot groups for filelock/tiktoken** | LOW | These fall outside current groups; will be individual PRs |
| **CI failures may be pre-existing** | LOW | Previous 10 PRs all showed CI failures from base branch issues |

---

## 9. Acciones Explícitamente NO Tomadas

1. ❌ `dependabot.yml` NOT recreated or modified
2. ❌ No PRs opened
3. ❌ No dependencies updated
4. ❌ No functional code touched
5. ❌ `pyproject.toml` NOT modified
6. ❌ `uv.lock` NOT modified
7. ❌ No branches or tags created/modified
8. ❌ No `--no-verify` used
9. ❌ No auto-merge enabled
10. ❌ No mypy floor update executed

---

## 10. Próximo Paso Recomendado

1. **Human review** of this policy document
2. **Approve or modify** the proposed dependabot.yml config
3. **Replace** `.github/dependabot.yml` with approved config (separate commit)
4. **Address mypy floor update** in a dedicated SDD cycle
5. **Address typer version gap** assessment (0.9 → 0.24 impact analysis)
6. **Close this follow-up** in hygiene README and authority registry

---

*Generated: 2026-05-09 | Status: DRAFT | Change: git-hygiene-dependabot-policy | No operational changes.*
