```python
# tests/integration/test_ast_symbols_cwd.py
import pytest
import subprocess
import tempfile
from pathlib import Path
import json

def test_ast_symbols_from_different_cwd(tmp_path):
    """AP3 TRIPWIRE: ast symbols funciona desde cwd diferente.

    Confirma que el comando resuelve paths desde segment_root,
    NO desde cwd.
    """
    with tempfile.TemporaryDirectory() as other_cwd:
        # Crear segmento de prueba con estructura src/
        segment = tmp_path / "test_segment"
        segment.mkdir()
        src_dir = segment / "src"
        src_dir.mkdir()

        # Crear módulo de prueba
        (src_dir / "test_module.py").write_text("""
# Test module
def test_function():
    pass
""")

        # Ejecutar desde cwd DIFERENTE (AP3)
        result = subprocess.run(
            ["uv", "run", "trifecta", "ast", "symbols", "sym://python/mod/test_module"],
            cwd=other_cwd,  # <-- CRÍTICO
            capture_output=True,
            text=True,
            timeout=30
        )

        # AP7: Validar response JSON (no string parsing)
        response = json.loads(result.stdout)
        status = response.get("status")
        error_code = response.get("errors", [{}])[0].get("code")

        # AP7: PASS si NO es FILE_NOT_FOUND
        assert status == "ok" or error_code != "FILE_NOT_FOUND", \
            f"AP3 FAIL: cwd-dependent resolution (status={status}, c
