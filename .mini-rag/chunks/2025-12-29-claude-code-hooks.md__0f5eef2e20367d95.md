### Task 1: Define the Run Record schema + update session template

**Files:**
- Modify: `src/infrastructure/templates.py`
- Modify: `tests/unit/test_session_protocol_templates.py`
- Optional Docs: `readme_tf.md`

**Step 1: Write failing test**

```python
# tests/unit/test_session_protocol_templates.py

def test_session_template_includes_run_record_schema():
    content = TemplateRenderer().render_session(config)
    assert "Run Record Schema" in content
    assert "run_id" in content
    assert "trifecta_sync" in content
    assert "final_status" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_session_protocol_templates.py -v`
Expected: FAIL with missing schema headings/fields.

**Step 3: Write minimal implementation**

```python
# src/infrastructure/templates.py
## Run Record Schema (append-only)
# - run_id
# - timestamp_start / timestamp_end / duration_ms
# - segment / invocation
# - user_intent / actions_summary
# - files_touched / commands_executed / tests_or_checks
# - trifecta_sync / trifecta_validate
# - lock / final_status
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_session_protocol_templates.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/infrastructure/templates.py tests/unit/test_session_protocol_templates.py readme_tf.md
git commit -m "docs: add session run record schema"
```
