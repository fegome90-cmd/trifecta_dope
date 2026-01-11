```python
# tests/integration/test_path_hygiene_e2e.py
import pytest
import subprocess
from pathlib import Path

def test_ctx_sync_produces_no_pii(tmp_path):
    """Integration: ctx sync NO genera PII en disco (AP2: tmp_path, AP3: no cwd dep).

    Este test:
    - Crea un segmento temporal (AP2: determinista)
    - Ejecuta el comando real `trifecta ctx sync`
    - Valida el JSON generado en disco
    - NO depende de cwd real del repo (AP3)
    """
    # Crear segmento temporal mínimo
    segment = tmp_path / "test_segment"
    segment.mkdir()
    (segment / "skill.md").write_text("# Test Skill")
    (segment / "agent.md").write_text("# Agent")
    (segment / "_ctx").mkdir()

    # Ejecutar sync real (subprocess, no imports Python)
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # AP7: FAIL cerrado si sync falla
    assert result.returncode == 0, f"sync failed: {result.stderr}"

    # Validar JSON generado en disco
    pack_path = segment / "_ctx" / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # AP7: Assertions explícitas (no grep en Python)
    assert "/Users/" not in content, f"PII leak detected"
    assert "/home/" not in content
    assert "file://" not in content
```
