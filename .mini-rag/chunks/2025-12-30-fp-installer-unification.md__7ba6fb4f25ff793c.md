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
