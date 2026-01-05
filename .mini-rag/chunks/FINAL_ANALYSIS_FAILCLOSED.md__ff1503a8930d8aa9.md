### Opción A: Dual Write Obligatorio (RECOMENDADO)

**Decisión**: V1 escribe a AMBOS destinos (telemetry.jsonl + session.md)

**Rationale**:
1. ✅ Mantiene backward compatibility 100%
2. ✅ Tests existentes pasan sin modificar
3. ✅ session.md sigue siendo historia humana legible
4. ✅ telemetry.jsonl se vuelve queryable source of truth
5. ✅ Cero regresión, solo extensión

**Implementación**:
```python
def session_append(...):
    # NUEVA Lógica: Write to telemetry
    telemetry.event(
        cmd="session.entry",
        args={"summary": summary, "type": "develop", "files": files_list, "commands": commands_list},
        result={"outcome": "success"},
        timing_ms=0,
        tags=[]
    )

    # EXISTENTE: Write to session.md (NO TOCAR)
    if not session_file.exists():
        session_file.write_text(header + entry_text)
    else:
        with open(session_file, "a") as f:
            f.write(entry_text)

    # Output text (backward compat)
    typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**Gate**: `pytest tests/unit/test_session_and_normalization.py -v` → 3/3 PASS

---
