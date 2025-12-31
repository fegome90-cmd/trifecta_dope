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
