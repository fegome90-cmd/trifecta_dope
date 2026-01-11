```python
# tests/integration/test_path_hygiene_e2e.py
import pytest
import subprocess
from pathlib import Path

def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco.

    v2.2 FIX: Usa nombres canónicos reales descubiertos via rg.
    """
    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    segment_name = "test_segment"  # Usado para prime/session filenames

    # v2.2: Crear archivos canónicos con nombres correctos
    (segment / "skill.md").write_text("""# Test Skill

## Rules
- Rule 1: Test rule
""")

    # Nota: agent.md puede llamarse README.md en algunas versiones
    # Verificar con rg cuál es el canónico
    (segment / "agent.md").write_text("""# Agent

Stack: Python 3.12+
Purpose: Integration test
""")

    # v2.2: Formato correcto: prime_<segment>.md, session_<segment>.md
    (segment / f"prime_{segment_name}.md").write_text(f"""# Prime {segment_name.title()}

## Reading Order
1. skill.md
2. agent.md
""")

    (segment / f"session_{segment_name}.md").write_text(f"""# Session {segment_name.title()}

## Handoff
- Entry: {pytest.current_time()}
""")

    (segment / "README.md").write_text(f"""# README

Context for {segment_name}
""")

    # Ejecutar sync real
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
