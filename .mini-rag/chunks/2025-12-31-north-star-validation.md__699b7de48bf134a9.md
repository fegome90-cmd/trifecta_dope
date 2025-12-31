```python
# In src/infrastructure/cli.py - build() command

from src.infrastructure.validators import validate_segment_fp

@ctx_app.command("build")
def build(...):
    path = Path(segment).resolve()
    
    # FP Gate: Pattern matching on Result
    match validate_segment_fp(path):
        case Err(errors):
            typer.echo("❌ Validation Failed (North Star Gate):")
            for err in errors:
                typer.echo(f"   - {err}")
            raise typer.Exit(code=1)
        case Ok(validation_result):
            # Check for legacy warnings
            legacy = detect_legacy_context_files(path)
            if legacy:
                typer.echo("⚠️  Legacy files detected (consider renaming):")
                for lf in legacy:
                    typer.echo(f"   - _ctx/{lf}")
    
    # ... rest of build logic
```

**Step 3.4: Run test**

Run: `uv run pytest tests/unit/test_cli_fp_gate.py -v`
Expected: PASS

**Step 3.5: Commit**

```bash
git add src/infrastructure/cli.py tests/unit/test_cli_fp_gate.py
git commit -m "feat(cli): Integrate FP validation gate with pattern matching"
```

---
