# Handoff: Skills Contracts + Explain - Post-Review Fixes

## Session: 2026-03-06
## Branch: `feat/skills-contracts-explain`
## Status: 🔄 READY TO IMPLEMENT

---

## Context

Completed thorough 4-agent code review (mr-thorough) on the Skills Contracts + Explain feature. Identified 3 actionable fixes before merge.

### Key Finding
The codebase uses `typer.echo()` + custom exceptions (no `logging` module). Silent `except Exception: continue` is a common pattern - keep it consistent.

---

## Pending Fixes (3 items)

### Fix 1: Add note to `parse_frontmatter` docstring
**File**: `src/infrastructure/skills_fs.py:31`
**Line**: 31-41
**Action**: Add note about silent YAML error handling

```python
def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full file content with optional frontmatter

    Returns:
        (frontmatter_dict, body_content)
        If no frontmatter, returns ({}, content)

    Note: YAML errors are silently caught and return empty frontmatter.
    This matches the codebase pattern of graceful degradation.
    """
```

---

### Fix 2: Add comment to `discover_skills_from_paths`
**File**: `src/infrastructure/skills_fs.py:170`
**Line**: 170-171
**Action**: Add inline comment explaining design decision

```python
try:
    content = path.read_text()
    frontmatter, _ = parse_frontmatter(content)
    meta = dict_to_skill_meta(frontmatter, str(path))
    skills.append(DiscoveredSkill(path=path, meta=meta, content=content))
except Exception:
    # Silently skip files that can't be read (permission, encoding, etc.)
    # Matches codebase pattern - see cli.py:200, cli.py:209 for similar patterns
    continue
```

---

### Fix 3: Refactor `execute_with_explanation`
**File**: `src/application/search_get_usecases.py:371`
**Action**: Add helper function `_build_disabled_lint_plan()`

Add this helper function after line 98 (after `_classify_zero_hit_reason`):

```python
def _build_disabled_lint_plan(normalized_query: str) -> LinterPlan:
    """Build a disabled lint plan for when linting is off."""
    return {
        "original_query": normalized_query,
        "query_class": "disabled",
        "token_count": 0,
        "anchors_detected": {"strong": [], "weak": [], "aliases_matched": []},
        "expanded_query": normalized_query,
        "changed": False,
        "changes": {"added_strong": [], "added_weak": [], "reasons": []},
    }
```

Then replace lines 417-426 in `execute_with_explanation` with:
```python
else:
    lint_plan = _build_disabled_lint_plan(normalized_query)
    query_for_expander = normalized_query
```

---

## Verification Commands

```bash
# Tests
uv run pytest tests/unit/test_skill_contracts_validation.py tests/integration/test_skill_lint_cli.py tests/integration/test_search_explain_json_contract.py -v

# Lint
uv run ruff check src/infrastructure/skills_fs.py src/application/search_get_usecases.py

# Type check
uv run mypy src/infrastructure/skills_fs.py src/application/search_get_usecases.py
```

---

## Current State

- Branch: `feat/skills-contracts-explain`
- Base commits: 6497143, 5f102fd, 4950183
- 36 tests passing
- CI gate added

---

## Prompt for Next Session

```
Continúa con los fixes del code review en la branch feat/skills-contracts-explain.

Lee el handoff en _ctx/handoff/SKILLS-CONTRACTS-REVIEW-FIXES.md

Los 3 fixes son:
1. Add docstring note to parse_frontmatter (skills_fs.py:31)
2. Add comment to discover_skills_from_paths (skills_fs.py:170)
3. Add _build_disabled_lint_plan helper (search_get_usecases.py)

Después de implementar, corre:
uv run pytest tests/unit/test_skill_contracts_validation.py tests/integration/test_skill_lint_cli.py tests/integration/test_search_explain_json_contract.py -v
```
