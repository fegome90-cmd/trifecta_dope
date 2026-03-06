# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix code quality issues identified in the code review for E-V1-WO1 platform layer code.

**Architecture:** Simple refactoring to fix import organization and add missing exports. No architectural changes.

**Tech Stack:** Python, ruff (linter)

---

## Issues to Fix

| Severity | File | Line | Issue |
|----------|------|------|-------|
| MEDIUM | `contracts.py` | 31, 53 | Duplicate `import hashlib` inside functions |
| MEDIUM | `contracts.py` | 66 | Redundant `from pathlib import Path` inside function |
| LOW | `__init__.py` | - | Constant `DEFAULT_FINGERPRINT_LENGTH` not exported |

---

## Task 1: Fix Duplicate Imports in contracts.py

**Files:**
- Modify: `src/platform/contracts.py:1-100`

**Step 1: Read current file to understand structure**

```bash
cat src/platform/contracts.py
```

**Step 2: Edit to move hashlib import to top-level**

Find and replace the duplicate imports inside functions with top-level import.

Current problematic code (lines 29-35):
```python
def compute_repo_id(canonical_path: Path, hash_length: int = DEFAULT_FINGERPRINT_LENGTH) -> str:
    """Compute stable repo_id from canonical path.
    ...
    """
    import hashlib

    path_str = str(canonical_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]
```

Replace with (add hashlib at top of file, remove from function):
```python
import hashlib
from pathlib import Path


DEFAULT_FINGERPRINT_LENGTH = 8


def compute_repo_id(canonical_path: Path, hash_length: int = DEFAULT_FINGERPRINT_LENGTH) -> str:
    path_str = str(canonical_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]
```

**Step 3: Remove duplicate from compute_runtime_key function**

Find and remove the `import hashlib` inside `compute_runtime_key`.

**Step 4: Remove redundant Path import in get_repo_runtime_dir**

Find and remove the redundant `from pathlib import Path` inside the function (already imported at top).

**Step 5: Run ruff to verify fixes**

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope && uv run ruff check src/platform/contracts.py
```

Expected: No errors

---

## Task 2: Add DEFAULT_FINGERPRINT_LENGTH to __all__

**Files:**
- Modify: `src/platform/__init__.py`

**Step 1: Add constant to __all__ list**

Add `"DEFAULT_FINGERPRINT_LENGTH",` to the `__all__` list in `src/platform/__init__.py`.

**Step 2: Run ruff to verify**

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope && uv run ruff check src/platform/__init__.py
```

Expected: No errors

---

## Task 3: Verify All Changes

**Step 1: Run full platform lint**

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope && uv run ruff check src/platform/
```

Expected: All checks passed

**Step 2: Run tests**

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope && uv run pytest -q tests/integration/runtime/ tests/integration/daemon/
```

Expected: All tests pass

---

## Task 4: Commit Changes

**Step 1: Stage and commit**

```bash
export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
git add src/platform/contracts.py src/platform/__init__.py
git commit -m "fix: organize imports in platform contracts and add missing export"
```

Expected: Commit successful

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-06-code-review-fixes.md`. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Direct Execution** - I'll execute the fixes directly now

**Which approach?**
