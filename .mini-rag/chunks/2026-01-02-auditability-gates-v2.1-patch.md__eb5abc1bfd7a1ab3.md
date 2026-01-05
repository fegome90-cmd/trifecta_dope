```python
# tests/integration/test_path_hygiene_e2e.py
def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco.

    v2.1: Crea segmento COMPLETO con archivos canónicos mínimos.
    """
    from pathlib import Path
    import subprocess

    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Crear archivos canónicos MÍNIMOS que Trifecta espera
    (segment / "skill.md").write_text("# Test Skill\n\n## Rules\n- Rule 1")
    (segment / "agent.md").write_text("# Agent\n\nStack: Python 3.12")
    (segment / "prime_segment.md").write_text("# Prime\n\n- Read skill.md")
    (segment / "session_segment.md").write_text("# Session\n\n## Handoff\n- Entry")
    (segment / "README.md").write_text("# README\n\nContext for segment")

    # Ejecutar sync real
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0, f"sync failed: {result.stderr}"

    pack_path = ctx_dir / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # AP7: Assertions explícitas
    assert "/Users/" not in content, f"PII leak: /Users/ found"
    assert "/home/" not in content
    assert "file://" no
