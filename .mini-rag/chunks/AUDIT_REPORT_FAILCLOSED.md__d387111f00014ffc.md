#### Step 1: Fix Backward Compatibility (Blocker #1)
**Tarea**: Modificar `session_append` para dual write

**Código**:
```python
# src/infrastructure/cli.py:L1280
@session_app.command("append")
def session_append(...):
    # ... existing code ...

    # NEW: Write to telemetry.jsonl
    from src.infrastructure.telemetry import Telemetry
    telemetry = Telemetry(root=segment_path)
    telemetry.event(
        cmd="session.entry",
        args={
            "summary": summary,
            "type": "develop",  # TODO: add --type flag in V1.1
            "files": files_list,
            "commands": commands_list
        },
        result={"outcome": "success"},  # TODO: add --outcome flag in V1.1
        timing_ms=0,
        tags=[]  # TODO: add --tags flag in V1.1
    )

    # EXISTING: Write to session.md (KEEP for backward compat)
    if not session_file.exists():
        session_file.write_text(...)
    else:
        with open(session_file, "a") as f:
            f.write(...)

    typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**Test Gate**:
```bash
pytest tests/unit/test_session_and_normalization.py -v
# MUST: 3/3 tests pass
```

**Verify**:
