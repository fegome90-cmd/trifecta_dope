#### Step 4: Validate with Schema (Blocker #2 continued)

**Test**:
```python
# tests/integration/test_session_query_schema.py
import json
import subprocess
from jsonschema import validate

def test_session_query_validates_against_schema():
    """Ensure session query output matches JSON schema."""
    with open("docs/schemas/session_query_clean.schema.json") as f:
        schema = json.load(f)

    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--last", "5"],
        capture_output=True, text=True, check=True
    )

    output = json.loads(result.stdout)
    validate(instance=output, schema=schema)  # Raises if invalid
    print("✅ Output validates against schema")
```

**Test Gate**:
```bash
pytest tests/integration/test_session_query_schema.py -v
# MUST pass
```

---
