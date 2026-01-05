```python
# tests/unit/test_path_hygiene.py
import pytest
from pathlib import Path
from src.domain.context_models import TrifectaPack

def test_sanitized_dump_removes_absolute_paths():
    """Unit: sanitized_dump() elimina TODOS los paths absolutos."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    # Simular chunks con paths absolutos (caso real problemático)
    pack.chunks = [
        {
            "id": "test",
            "text": "content",
            "source_path": "/Users/felipe/Developer/agent_h/some/file.py",  # PATH PROBLEMÁTICO
        }
    ]

    json_str = pack.sanitized_dump()

    # AP7: Assertions explícitas (PASS solo si NO hay PII)
    assert "/Users/" not in json_str, f"PII leak /Users/: {json_str[:500]}"
    assert "/home/" not in json_str
    assert "file://" not in json_str
    assert "<RELATIVE>" in json_str or "<ABS_PATH_REDACTED>" in json_str

def test_sanitized_dump_relative_paths_ok():
    """Unit: paths relativos se preservan."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    json_str = pack.sanitized_dump()

    # Paths relativos NO deben ser redactados
