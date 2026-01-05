```python
# tests/integration/test_path_hygiene_e2e.py
def test_ctx_sync_produces_no_pii(tmp_path, monkeypatch):
    """Integration: ctx sync NO genera PII en disco."""
    from src.application.use_cases import BuildContextPackUseCase
    from src.infrastructure.file_system import FileSystemAdapter
    from pathlib import Path
    import subprocess

    # Crear segmento temporal
    segment = tmp_path / "test_segment"
    segment.mkdir()
    (segment / "skill.md").write_text("# Test")

    # Ejecutar sync real
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"sync failed: {result.stderr}"

    # Validar JSON generado
    pack_path = segment / "_ctx" / "context_pack.json"
    assert pack_path.exists()
    content = pack_path.read_text()
    assert "/Users/" not in content
    assert "/home/" not in content
    assert "file://" not in content
```

**DoD:**
- [ ] Unit test `test_context_pack_sanitized_dump_no_pii` pasa
- [ ] Integration test `test_ctx_sync_produces_no_pii` pasa
- [ ] Manual: `rg -n '"/Users/' _ctx/context_pack.json; echo RC=$?` retorna 1
- [ ] Commit: "fix(g2): sanitize paths in context_pack.json"

---
