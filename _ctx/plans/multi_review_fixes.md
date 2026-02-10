# Plan: Fix Multi-Review Findings from Nivel A Integration

**Context**: After completing the G0 gates for Sidecar integration, a multi-review identified **11 issues** that need to be addressed before proceeding to Nivel B.

**Date**: 2026-02-10
**WO**: WO-0011
**Epic**: E-0002 (Code Quality & Technical Debt)

---

## Executive Summary

The multi-review of the Nivel A integration (moving worktrees outside repo) revealed:
- **3 CRITICAL issues** that must be fixed immediately
- **4 IMPORTANT issues** that should be addressed
- **4 SUGGESTIONS** for code quality improvements

**Most Critical**: The test `test_worktree_path_generation` is **BROKEN** and will fail.

---

## Issue Breakdown

### CRITICAL Issues (Must Fix)

| ID | Issue | File | Confidence | Impact |
|----|-------|------|------------|--------|
| C1 | Broken test expects worktree inside repo | tests/test_wo_orchestration.py:100 | 100% | Test fails |
| C2 | No validation that parent exists/writable | scripts/paths.py:119-139 | 95% | Cryptic errors |
| C3 | Dead code - try/except always fails | scripts/ctx_wo_take.py:304-312 | 90% | Misleading code |

### IMPORTANT Issues (Should Fix)

| ID | Issue | File | Confidence | Impact |
|----|-------|------|------------|--------|
| I1 | Parameter order inconsistency | scripts/helpers.py:100-115 | 95% | Confusing |
| I2 | No unit tests for get_worktree_path() | tests/unit/ (missing) | 100% | No coverage |
| I3 | Untested path conversion logic | scripts/ctx_wo_take.py:304-312 | 95% | Edge cases |
| I4 | No tests for updated regex | scripts/metadata_inference.py:225 | 100% | Silent failures |

### SUGGESTIONS (Nice to Have)

| ID | Issue | File | Confidence | Impact |
|----|-------|------|------------|--------|
| S1 | Inline import in exception handler | scripts/ctx_wo_take.py:309 | 85% | Style |
| S2 | Migrate from deprecated helpers | Multiple files | 80% | Tech debt |
| S3 | Regex validation logging | scripts/metadata_inference.py:225 | 60% | Debugging |
| S4 | Repo at filesystem root edge case | scripts/paths.py:119-139 | 90% | Rare edge case |

---

## Detailed Fixes

### C1: Fix Broken Test (CRITICAL)

**File**: `tests/test_wo_orchestration.py:100`

**Current**:
```python
expected = self.repo_root / ".worktrees" / self.test_wo_id
```

**Fix**:
```python
expected = self.repo_root.parent / ".worktrees" / self.test_wo_id
```

**Verification**: `uv run pytest tests/test_wo_orchestration.py::WOOrchestrationTest::test_worktree_path_generation -v`

---

### C2: Add Parent Directory Validation (CRITICAL)

**File**: `scripts/paths.py:get_worktree_path()`

**Add validation**:
```python
def get_worktree_path(root: Path, wo_id: str) -> Path:
    """Get the path to a WO's worktree directory.

    Raises:
        FileNotFoundError: If parent directory doesn't exist
        PermissionError: If parent directory is not writable
    """
    parent = root.parent

    # Validate parent directory exists
    if not parent.exists():
        raise FileNotFoundError(
            f"Cannot create worktree outside repo: parent directory does not exist\n"
            f"  Repository root: {root}\n"
            f"  Expected parent: {parent}"
        )

    # Validate parent directory is writable
    import os
    if not os.access(parent, os.W_OK):
        raise PermissionError(
            f"Cannot create worktree outside repo: parent directory is not writable\n"
            f"  Parent directory: {parent}\n"
            f"  Please check permissions: ls -la {parent.parent}"
        )

    return parent / _WORKTREES_DIR / wo_id
```

---

### C3: Simplify Dead Try/Except (CRITICAL)

**File**: `scripts/ctx_wo_take.py:304-312`

**Current** (dead code - try always fails):
```python
try:
    worktree = str(auto_worktree.relative_to(root))
except ValueError:
    import os
    worktree = os.path.relpath(auto_worktree, root)
```

**Fix** (simplify - always use relpath):
```python
import os  # Move to top of file (line ~11)

# ... later in code ...

# Worktree is outside repo - compute relative path from repo root
worktree = os.path.relpath(auto_worktree, root)
logger.info(f"  worktree (relative to repo): {worktree}")
```

**Rationale**: Since worktrees are ALWAYS outside repo, `Path.relative_to()` will ALWAYS raise `ValueError`. The try/except is unnecessary complexity.

---

### I1: Resolve Parameter Order Inconsistency (IMPORTANT)

**Options**:

**Option A**: Update helpers.py to match paths.py signature
```python
# In helpers.py line 100
def get_worktree_path(root: Path, wo_id: str) -> Path:
    """DEPRECATED: Use scripts.paths.get_worktree_path() instead."""
    from scripts.paths import get_worktree_path as _get_worktree_path
    return _get_worktree_path(root, wo_id)
```

Then update all call sites (helpers.py:212, 282, 644; ctx_wo_take.py:292; test_wo_orchestration.py:99, 223).

**Option B**: Add explicit alias to avoid shadowing
```python
# In helpers.py imports
from scripts.paths import (
    get_lock_path,
    get_wo_pending_path,
    get_wo_running_path,
    get_worktree_path as paths_get_worktree_path,  # Explicit alias
    get_branch_name,
)
```

**Recommendation**: Option A (align signatures) for consistency.

---

### I2: Add Unit Tests for get_worktree_path() (IMPORTANT)

**Create**: `tests/unit/test_paths.py`

```python
import tempfile
from pathlib import Path
import pytest
from scripts.paths import get_worktree_path


def test_get_worktree_path_outside_repo():
    """Test that worktrees are created outside the repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate repo at /tmp/test_repo
        repo_root = Path(tmpdir) / "test_repo"
        repo_root.mkdir()

        # Worktree should be at /tmp/.worktrees/WO-0001
        worktree_path = get_worktree_path(repo_root, "WO-0001")
        expected = Path(tmpdir) / ".worktrees" / "WO-0001"

        assert worktree_path == expected
        # Verify worktree is NOT inside repo
        assert not worktree_path.is_relative_to(repo_root)


def test_get_worktree_path_multiple_wos():
    """Test that multiple WO paths are correctly generated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        wo_ids = ["WO-0001", "WO-0002", "WO-0018A"]
        for wo_id in wo_ids:
            path = get_worktree_path(repo_root, wo_id)
            assert path == Path(tmpdir) / ".worktrees" / wo_id
            assert not path.is_relative_to(repo_root)


def test_get_worktree_path_parent_does_not_exist():
    """Test that FileNotFoundError is raised when parent doesn't exist."""
    # This would require mocking or creating a special scenario
    # For now, document that this should be tested
    pass


def test_get_worktree_path_parent_not_writable():
    """Test that PermissionError is raised when parent is not writable."""
    # This would require mocking os.access
    # For now, document that this should be tested
    pass
```

---

### I3: Add Tests for Path Conversion Logic (IMPORTANT)

**Create**: `tests/unit/test_ctx_wo_take.py`

```python
import tempfile
from pathlib import Path
from scripts.paths import get_worktree_path
import os


def test_worktree_relative_path_conversion():
    """Test conversion from absolute to relative path for git commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Simulate the path conversion logic
        auto_worktree = get_worktree_path(repo_root, "WO-0001")

        # Test relative path calculation
        worktree = os.path.relpath(auto_worktree, repo_root)

        # Should be "../.worktrees/WO-0001"
        assert worktree == "../.worktrees/WO-0001"


def test_worktree_relative_path_nested_repo():
    """Test relative path when repo is in nested directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Repo at /tmp/test/deep/repo
        repo_root = Path(tmpdir) / "test" / "deep" / "repo"
        repo_root.mkdir(parents=True)

        auto_worktree = get_worktree_path(repo_root, "WO-0001")
        worktree = os.path.relpath(auto_worktree, repo_root)

        # Should be "../../.worktrees/WO-0001"
        assert worktree == "../../.worktrees/WO-0001"
```

---

### I4: Add Tests for Metadata Inference Regex (IMPORTANT)

**Create**: `tests/unit/test_metadata_inference.py`

```python
from pathlib import Path
from unittest.mock import patch
from scripts.metadata_inference import get_worktrees_from_git


def test_get_worktrees_from_git_outside_repo():
    """Test parsing git worktree list output for worktrees outside repo."""
    # Mock git output with worktree outside repo
    git_output = """/dev/.worktrees/WO-0018 abc123 [feat/wo-WO-0018B]
/dev/repo feat/wo-WO-0019 def456"""

    with patch("subprocess.check_output", return_value=git_output.encode()):
        worktrees = get_worktrees_from_git(Path("/dev/repo"))

        assert "WO-0018B" in worktrees
        assert worktrees["WO-0018B"]["path"] == "/dev/.worktrees/WO-0018"
        assert worktrees["WO-0018B"]["branch"] == "feat/wo-WO-0018B"


def test_get_worktrees_from_git_relative_path():
    """Test parsing worktree with relative path."""
    git_output = """../.worktrees/WO-0010 abc123 [feat/wo-WO-0010]
/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope feat/wo-WO-0011 def456"""

    with patch("subprocess.check_output", return_value=git_output.encode()):
        worktrees = get_worktrees_from_git(
            Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope")
        )

        assert "WO-0010" in worktrees
        assert worktrees["WO-0010"]["path"] == "../.worktrees/WO-0010"
```

---

## Implementation Order

1. **Phase 1 (CRITICAL)**: Fix C1, C2, C3
   - T1: Fix broken test (C1)
   - T3: Add validation (C2)
   - T6: Simplify dead code (C3)

2. **Phase 2 (IMPORTANT)**: Add tests for new behavior
   - T2: Add unit tests for get_worktree_path() (I2)
   - T4: Add tests for metadata inference (I4)
   - T5: Add tests for path conversion (I3)

3. **Phase 3 (CLEANUP)**: Resolve technical debt
   - T7: Resolve parameter order (I1)
   - T8: Update integration test mocks (S2)

---

## Verification Commands

```bash
# Run all new and modified tests
uv run pytest tests/unit/test_paths.py \
              tests/unit/test_metadata_inference.py \
              tests/unit/test_ctx_wo_take.py \
              tests/test_wo_orchestration.py -v

# Run full test suite
uv run pytest -m "not slow" --cov=scripts/paths --cov=scripts/metadata_inference --cov=scripts/ctx_wo_take
```

---

## Related Documentation

- Original integration plan: `_ctx/plans/eager-wibbling-token.md`
- WO system docs: `docs/backlog/WORKFLOW.md`
- Sidecar integration: G0 gates (all PASSED)

---

## Notes

- All agents agreed on the critical findings
- The parameter order issue was flagged by 3 different agents
- The dead try/except was discovered by the simplification agent
- Test coverage was identified as the biggest gap
