# CI Quality Improvements - Phase 2

> **Continuation of:** [2026-03-15-ci-quality-improvements.md](./2026-03-15-ci-quality-improvements.md)

## Current State (After Phase 1)

| Metric | Value |
|--------|-------|
| Total mypy errors | 177 |
| type-arg errors | 51 |
| unused-ignore errors | 9 |
| no-untyped-def | ~31 |
| no-untyped-call | ~34 |
| no-any-return | ~13 |

## Phase 2 Goals

Resolve remaining mypy strict errors to reach <100 total errors.

## Task 1: Fix Remaining unused-ignore Errors

**Files:** 9 files with unnecessary `# type: ignore` comments

**Commands:**
```bash
# List all unused-ignore errors
uv run mypy src/ --strict 2>&1 | grep "unused-ignore"
```

**Files to fix:**
- `src/application/plan_use_case.py:139`
- `src/application/use_cases.py:9`
- `src/domain/obsidian_models.py:256,258`
- `src/infrastructure/aliases_fs.py:20`
- `src/infrastructure/cli_skills.py:20`
- `src/infrastructure/cli_ast.py:1`
- `src/infrastructure/cli.py:12`
- `src/infrastructure/obsidian_config.py:24`

**Verification:**
```bash
uv run mypy src/ --strict 2>&1 | grep -c "unused-ignore"
# Expected: 0
```

---

## Task 2: Fix type-arg Errors (Batch 3 - Application Layer)

**Files:**
- `src/application/stub_regen_use_case.py:115,117,153`
- `src/application/plan_use_case.py:115,135,171`

**Pattern:** Change `dict` → `dict[str, Any]`

**Verification:**
```bash
uv run mypy src/application/ --strict 2>&1 | grep "type-arg"
# Expected: No type-arg errors
```

---

## Task 3: Fix type-arg Errors (Batch 4 - Infrastructure)

**Files:**
- `src/platform/runtime_manager.py:42,54`
- `src/domain/linear_models.py:28`

**Verification:**
```bash
uv run mypy src/platform/ src/domain/linear_models.py --strict 2>&1 | grep "type-arg"
# Expected: No type-arg errors
```

---

## Task 4: Document no-untyped-def Strategy

**Context:** 31 errors of type `no-untyped-def`

These require function-level type annotations. Options:

1. **Minimal approach:** Add `-> None` and basic arg types only
2. **Full approach:** Complete type signatures with proper generics
3. **Ignore approach:** Add to mypy config if not critical

**Recommendation:** Minimal approach for domain layer, full approach for public APIs.

**Files with most errors:**
```bash
uv run mypy src/ --strict 2>&1 | grep "no-untyped-def" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

---

## Task 5: Baseline Safety Vulnerabilities

**Current:** 3 known vulnerabilities in dependencies

**Vulnerabilities:**
- `urllib3` (CVE-2026-21441) - DoS via redirect handling
- `filelock` (PVE-2026-84183) - TOCTOU Race Condition  
- `filelock` (CVE-2026-22701) - TOCTOU Race Condition

**Actions:**
1. Document in `docs/technical_guides/dependency_vulnerabilities.md`
2. Evaluate if upgrades are possible without breaking changes
3. Add to weekly CI check for monitoring

**Command:**
```bash
uv run safety check --json > docs/technical_guides/vulnerability_baseline.json
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Total mypy errors | <100 |
| type-arg errors | 0 |
| unused-ignore errors | 0 |
| Safety vulnerabilities | Documented with remediation plan |
| All tests passing | ✅ |

## References

- Original plan: [2026-03-15-ci-quality-improvements.md](./2026-03-15-ci-quality-improvements.md)
- Query expansion docs: [query_expansion_systems.md](../technical_guides/query_expansion_systems.md)
