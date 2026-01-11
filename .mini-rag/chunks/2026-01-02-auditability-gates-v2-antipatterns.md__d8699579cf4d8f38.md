```python
# tests/unit/test_path_hygiene.py
import pytest
from pathlib import Path
from src.domain.context_models import TrifectaPack

def test_sanitized_dump_removes_absolute_paths():
    """Unit: sanitized_dump() elimina paths absolutos (AP2: fixture determinista)."""
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )

    json_str = pack.sanitized_dump()

    # AP7: PASS/FAIL por asserts explícitos
    assert "/Users/" not in json_str, f"PII leak: /Users/ found in {json_str[:200]}"
    assert "/home/" not in json_str
    assert "file://" not in json_str
    assert "<REPO_ROOT>" in json_str
    assert "<FILE_URI_SANITIZED>" not in json_str  # No debería haber file:// URIs
```

**Integration test (AP2: tmp_path, AP3: no cwd dependency):**
