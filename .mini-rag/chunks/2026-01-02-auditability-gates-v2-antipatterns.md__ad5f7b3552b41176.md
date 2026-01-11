**CWD Independence test (AP3 TRIPWIRE):**
```python
# tests/integration/test_cwd_independence.py
import pytest
import subprocess
import tempfile
from pathlib import Path

def test_ctx_sync_from_different_cwd():
    """AP3 TRIPWIRE: ctx sync funciona desde cwd diferente.

    Este test es CRÍTICO para detectar dependencias implícitas en cwd.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        other_cwd = Path(temp_dir) / "other_location"
        other_cwd.mkdir()

        # Crear segmento en path absoluto
        with tempfile.TemporaryDirectory() as segment_dir:
            segment = Path(segment_dir) / "test_segment"
            segment.mkdir()
            (segment / "skill.md").write_text("# Test")

            # Ejecutar desde cwd DIFERENTE
            result = subprocess.run(
                ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
                cwd=other_cwd,  # <-- AP3: cwd diferente
                capture_output=True,
                text=True
            )

            # AP7: FAIL si depende de cwd
            assert result.returncode == 0, f"cwd-dependent: {result.stderr}"

            pack_path = segment / "_ctx" / "context_pack.json"
            assert pack_path.exists()
            content = pack_path.read_text()
            assert "/Users/" not in content
```
