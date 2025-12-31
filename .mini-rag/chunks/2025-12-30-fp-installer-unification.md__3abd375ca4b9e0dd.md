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
