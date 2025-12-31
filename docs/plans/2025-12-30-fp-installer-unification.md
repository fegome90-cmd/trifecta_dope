# FP Installer Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `scripts/install_FP.py` the canonical installer by adding missing validations and legacy-name warnings while keeping dynamic naming and no auto-renames.

**Architecture:** Add a pure validation helper in `src/infrastructure/validators.py` to detect legacy context filenames, and wire it into the FP installer. Keep installation side effects in the script and keep validators pure.

**Tech Stack:** Python 3.12, Typer CLI (indirect), pytest, uv

### Task 1: Add legacy-name detection tests (TDD red)

**Files:**
- Modify: `tests/unit/test_validators.py`

**Step 1: Write the failing test**

```python
    def test_detect_legacy_context_files(self, temp_segment_dir: Path) -> None:
        """
        Scenario: Segment has legacy files (agent.md, prime.md, session.md) in _ctx.
        Expected: detect_legacy_context_files returns those filenames.
        """
        from src.infrastructure.validators import detect_legacy_context_files

        seg = temp_segment_dir / "legacyseg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent.md").touch()
        (ctx / "prime.md").touch()
        (ctx / "session.md").touch()

        legacy = detect_legacy_context_files(seg)
        assert set(legacy) == {"agent.md", "prime.md", "session.md"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_validators.py::TestValidateSegmentStructureContract::test_detect_legacy_context_files -v`
Expected: FAIL with `ImportError` or `NameError` because `detect_legacy_context_files` is missing.

### Task 2: Implement legacy-name detection (TDD green)

**Files:**
- Modify: `src/infrastructure/validators.py`

**Step 1: Write minimal implementation**

```python
def detect_legacy_context_files(path: Path) -> List[str]:
    """
    Detect legacy (non-dynamic) context filenames inside _ctx.
    Returns a list of legacy filenames that exist, in stable order.
    """
    legacy_names = ["agent.md", "prime.md", "session.md"]
    ctx_dir = path / "_ctx"
    if not ctx_dir.exists():
        return []
    found = [name for name in legacy_names if (ctx_dir / name).exists()]
    return found
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_validators.py::TestValidateSegmentStructureContract::test_detect_legacy_context_files -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/infrastructure/validators.py tests/unit/test_validators.py
git commit -m "feat: detect legacy context filenames"
```

### Task 3: Add cli-root validation and legacy warning in installer

**Files:**
- Modify: `scripts/install_FP.py`

**Step 1: Write failing test (installer behavior)**

```python
def test_install_fp_warns_on_legacy_names(tmp_path: Path, capsys) -> None:
    # Create fake CLI root with pyproject.toml
    cli_root = tmp_path / "cli"
    cli_root.mkdir()
    (cli_root / "pyproject.toml").write_text("[project]\nname='trifecta'\n")

    # Create legacy segment
    seg = tmp_path / "legacyseg"
    seg.mkdir()
    (seg / "skill.md").touch()
    ctx = seg / "_ctx"
    ctx.mkdir()
    (ctx / "agent.md").touch()
    (ctx / "prime.md").touch()
    (ctx / "session.md").touch()

    # Call the warning helper (or main entry) to assert warning text
    from scripts.install_FP import _format_legacy_warning
    warning = _format_legacy_warning(seg, ["agent.md", "prime.md", "session.md"])
    assert "legacy" in warning.lower()
    assert "agent.md" in warning
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/installer_test.py::test_install_fp_warns_on_legacy_names -v`
Expected: FAIL because helper doesn’t exist.

**Step 3: Implement installer changes**

- Add `pyproject.toml` check for `cli_root` with clear error message and exit code 1.
- Import and call `detect_legacy_context_files` per segment.
- If legacy names found, print a warning advising to rename to dynamic names; do not modify files.
- Optionally print stdout from `trifecta ctx sync` (for parity with old installer).
- Keep validation fail-fast behavior and return codes as in current FP installer.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/installer_test.py::test_install_fp_warns_on_legacy_names -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/install_FP.py tests/installer_test.py
git commit -m "feat: warn on legacy context filenames in installer"
```

### Task 4: Full validation run

**Files:**
- None (verification)

**Step 1: Run targeted tests**

Run: `uv run pytest tests/unit/test_validators.py tests/installer_test.py -v`
Expected: PASS

**Step 2: Run optional gates**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Commit (if needed)**

```bash
git add -A
git commit -m "chore: validate fp installer changes"
```
