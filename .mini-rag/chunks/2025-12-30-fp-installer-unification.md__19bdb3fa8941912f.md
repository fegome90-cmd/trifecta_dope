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
