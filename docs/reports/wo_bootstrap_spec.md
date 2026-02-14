# WO Bootstrap + Preflight Specification

**Generated:** 2026-02-14
**Status:** Draft
**Source:** WO Lifecycle (Start) — Repo Map

---

## Executive Summary

Two new scripts to eliminate manual WO YAML authoring errors:

| Script | Purpose | Side Effects |
|--------|---------|--------------|
| `ctx_wo_bootstrap.py` | Create WO scaffold with all required fields | Creates `pending/WO-XXXX.yaml` |
| `ctx_wo_preflight.py` | Validate WO before take (dry-run) | None (read-only) |

**Key Design Decision:** Both scripts **reuse the existing linter** via import (`ctx_wo_lint.run()`), not subprocess. This ensures zero duplication of validation logic.

---

## A) CLI UX

### ctx_wo_bootstrap.py

```bash
# Minimum required
uv run python scripts/ctx_wo_bootstrap.py \
  --id WO-0047 \
  --epic E-0001 \
  --title "Feature description" \
  --priority P1 \
  --dod DOD-DEFAULT \
  --scope-allow "src/**" "tests/**" \
  --scope-deny ".env*" \
  --verify-cmd "scripts/verify.sh"

# With optional fields
uv run python scripts/ctx_wo_bootstrap.py \
  --id WO-0048 \
  --epic E-0002 \
  --title "Another feature" \
  --priority P2 \
  --dod DOD-STRICT \
  --scope-allow "src/api/**" \
  --scope-deny ".env*" "**/production.*" \
  --verify-cmd "uv run pytest -q" \
  --verify-cmd "ruff check src" \
  --deps WO-0047 \
  --register-epic \
  --dry-run
```

**Arguments:**

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `--id` | Yes | - | WO identifier (WO-XXXX) |
| `--epic` | Yes | - | Parent epic ID (E-XXXX) |
| `--title` | Yes | - | Descriptive title |
| `--priority` | No | `P2` | P0/P1/P2/P3 or critical/high/medium/low |
| `--dod` | No | `DOD-DEFAULT` | Definition of Done ID |
| `--scope-allow` | No | `["src/**", "tests/**", "docs/**"]` | Allow patterns |
| `--scope-deny` | No | `[".env*", "**/production.*"]` | Deny patterns |
| `--verify-cmd` | No | `["scripts/verify.sh"]` | Verification commands (repeatable) |
| `--deps` | No | - | Dependencies (repeatable WO IDs) |
| `--register-epic` | No | False | Add WO to epic's wo_queue in backlog.yaml |
| `--dry-run` | No | False | Show YAML without writing |
| `--root` | No | `.` | Repository root |

### ctx_wo_preflight.py

```bash
# Validate a pending WO
uv run python scripts/ctx_wo_preflight.py WO-0047

# Validate a specific path
uv run python scripts/ctx_wo_preflight.py _ctx/jobs/pending/WO-0047.yaml

# JSON output for CI
uv run python scripts/ctx_wo_preflight.py WO-0047 --json
```

**Arguments:**

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `wo_ref` | Yes | - | WO ID or path to YAML |
| `--json` | No | False | Output as JSON |
| `--root` | No | `.` | Repository root |

---

## B) Field Auto-Generation

### Fields Filled Automatically

| Field | Value | Source |
|-------|-------|--------|
| `version` | `1` | Hardcoded (current schema version) |
| `status` | `pending` | Always for new WOs |
| `owner` | `null` | Filled by `ctx_wo_take.py` |
| `branch` | `null` | Filled by `ctx_wo_take.py` |
| `worktree` | `null` | Filled by `ctx_wo_take.py` |
| `started_at` | `null` | Filled by `ctx_wo_take.py` |
| `finished_at` | `null` | Filled by `ctx_wo_finish.py` |
| `execution.engine` | `trifecta` | Required by contract |
| `execution.segment` | `.` | Required by contract |
| `execution.required_flow` | `[session.append:intent, ctx.sync, ctx.search, ctx.get, session.append:result]` | Mandatory 5 steps |

### Fields Required from User

| Field | Validation |
|-------|------------|
| `id` | Must match `^WO-[A-Za-z0-9.-]+$`, must not exist |
| `epic_id` | Must exist in `backlog.yaml` |
| `title` | Non-empty, warning if < 6 chars |
| `priority` | `P0|P1|P2|P3` or `critical|high|medium|low` |
| `dod_id` | Must exist in `_ctx/dod/*.yaml` |
| `scope.allow` | Non-empty list |
| `scope.deny` | Can be empty list |
| `verify.commands` | Non-empty list of strings |

---

## C) Template Strategy

**Decision:** Use **internal template** (not `template_jobs.yaml`).

**Rationale:**
- `template_jobs.yaml` has stale/example values that may confuse users
- Internal template is version-controlled and self-documenting
- Easier to enforce canonical key order

**Internal template structure:**

```python
WO_TEMPLATE = {
    "version": 1,
    "id": None,           # Required from user
    "epic_id": None,      # Required from user
    "title": None,        # Required from user
    "priority": "P2",
    "status": "pending",
    "owner": None,
    "branch": None,
    "worktree": None,
    "scope": {
        "allow": ["src/**", "tests/**", "docs/**"],
        "deny": [".env*", "**/production.*"],
    },
    "verify": {
        "commands": ["scripts/verify.sh"],
    },
    "dod_id": "DOD-DEFAULT",
    "execution": {
        "engine": "trifecta",
        "segment": ".",
        "required_flow": [
            "session.append:intent",
            "ctx.sync",
            "ctx.search",
            "ctx.get",
            "session.append:result",
        ],
    },
}
```

---

## D) Linter Integration

### Import vs Subprocess

**Decision:** Use **import** for `ctx_wo_lint`, **subprocess** for `ctx_wo_fmt`.

```python
# Import (same process)
from ctx_wo_lint import run as lint_run, Finding

findings: list[Finding] = lint_run(root, strict=True, wo_id=wo_id)
has_errors = any(f.severity == "ERROR" for f in findings)
```

**Why import for lint:**
- `ctx_wo_lint.run()` returns typed `list[Finding]`
- No JSON parsing needed
- Faster (no subprocess overhead)

**Why subprocess for fmt:**
- `ctx_wo_fmt.py` modifies files in-place
- subprocess isolates side effects
- Already designed as CLI tool

### Fail-Closed Guarantees

1. **Bootstrap must fail** if generated WO doesn't pass `wo-lint --strict`
2. **Bootstrap must fail** if generated WO doesn't pass `wo-fmt-check`
3. **No partial artifacts** — if validation fails, delete the created file
4. **Dry-run always validates** — `--dry-run` runs lint/fmt-check but doesn't write

---

## E) Integration with Makefile

```makefile
# Add to Makefile
wo-new:
	$(UV) python scripts/ctx_wo_bootstrap.py $(ARGS)

wo-preflight:
	$(UV) python scripts/ctx_wo_preflight.py $(WO)
```

---

## F) Test Plan

### Test Cases

| Test | Expected |
|------|----------|
| `test_bootstrap_creates_valid_wo` | YAML created, passes lint + fmt |
| `test_bootstrap_dry_run_no_file` | No file created |
| `test_bootstrap_missing_verify_fails` | Exit 1, clear error message |
| `test_bootstrap_epic_not_found` | Exit 1 before creating file |
| `test_bootstrap_wo_exists` | Exit 1, error about duplicate |
| `test_bootstrap_with_deps` | YAML includes dependencies |
| `test_preflight_valid_wo` | Exit 0, JSON output |
| `test_preflight_invalid_wo` | Exit 1, JSON with findings |

### Fixtures

```python
# tests/conftest.py
@pytest.fixture
def tmp_repo(tmp_path):
    """Create minimal repo structure with backlog, dod, schema."""
    # _ctx/backlog/backlog.yaml with E-TEST
    # _ctx/dod/dod-default.yaml with DOD-DEFAULT
    # docs/backlog/schema/work_order.schema.json
    # scripts/ctx_wo_lint.py (symlink or copy)
```

### Golden Snapshot

```python
# tests/test_wo_bootstrap.py
def test_golden_valid_wo_output(snapshot, tmp_repo):
    """Snapshot the exact YAML output for a valid WO."""
    result = run_bootstrap(tmp_repo, wo_id="WO-9999", ...)
    assert result.exit_code == 0
    snapshot.assert_match(result.yaml_output, "valid_wo.yaml")
```

---

## G) Error Messages

| Code | Message |
|------|---------|
| `WO_EXISTS` | `WO {id} already exists in {state}/ directory` |
| `EPIC_NOT_FOUND` | `Epic {epic_id} not found. Available: {epic_ids}` |
| `DOD_NOT_FOUND` | `DoD {dod_id} not found. Available: {dod_ids}` |
| `LINT_FAILED` | `Generated WO failed lint validation. This is a bug in bootstrap.` |
| `FMT_FAILED` | `Generated WO failed format check. This is a bug in bootstrap.` |

---

## H) Output Format

### Bootstrap (success)

```
✓ Created: _ctx/jobs/pending/WO-0047.yaml

WO ID:     WO-0047
Epic:      E-0001
Priority:  P1
Title:     Feature description

Validation:
  ✓ Schema: PASS
  ✓ Lint: PASS
  ✓ Format: PASS

Next steps:
  1. Review: cat _ctx/jobs/pending/WO-0047.yaml
  2. Take: uv run python scripts/ctx_wo_take.py WO-0047
```

### Preflight (success)

```
✓ WO-0047 passes all validation gates

Checks:
  ✓ Schema validation
  ✓ Execution contract
  ✓ Epic ID reference
  ✓ DoD reference
  ✓ Scope structure
  ✓ Verify commands
  ✓ Dependencies

Ready to take: uv run python scripts/ctx_wo_take.py WO-0047
```

---

## I) Implementation Checklist

- [ ] `scripts/ctx_wo_bootstrap.py`
  - [ ] Argument parsing
  - [ ] Template generation
  - [ ] Epic/DoD validation (pre-write)
  - [ ] File creation
  - [ ] Lint integration (import)
  - [ ] Fmt integration (subprocess)
  - [ ] `--dry-run` mode
  - [ ] `--register-epic` flag
- [ ] `scripts/ctx_wo_preflight.py`
  - [ ] WO resolution (ID or path)
  - [ ] Lint integration (import)
  - [ ] JSON output
- [ ] `tests/test_wo_bootstrap.py`
  - [ ] Fixtures
  - [ ] Test cases
  - [ ] Golden snapshots
- [ ] Makefile updates
- [ ] docs/backlog/WORKFLOW.md update

---

## J) Open Questions

1. **Should `--register-epic` be default?** Currently opt-in to avoid surprising file modifications.
2. **Should bootstrap auto-format?** Currently uses canonical key order, but could run `wo-fmt` after creation.
3. **How to handle `scope.override` for wildcards?** Bootstrap could auto-detect `*` and prompt for override fields.
