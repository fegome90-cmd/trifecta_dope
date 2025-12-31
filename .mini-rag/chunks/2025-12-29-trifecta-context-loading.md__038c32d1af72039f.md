#### 3. **Health Validation** (schema + invariantes)

**De**: supervisor-agent/health-validator  
**Para Trifecta**: Validador de context_pack.json

```python
def validate_context_pack(pack_path: Path) -> ValidationResult:
    """Validate context pack structure and invariants."""
    errors = []
    
    pack = json.loads(pack_path.read_text())
    
    # Schema version
    if pack.get("schema_version") != "1.0":
        errors.append(f"Unsupported schema: {pack.get('schema_version')}")
    
    # Index integrity
    chunk_ids = {c["id"] for c in pack["chunks"]}
    for entry in pack["index"]:
        if entry["id"] not in chunk_ids:
            errors.append(f"Index references missing chunk: {entry['id']}")
    
    # Token estimates
    for chunk in pack["chunks"]:
        if chunk.get("token_est", 0) < 0:
            errors.append(f"Negative token_est in chunk: {chunk['id']}")
    
    return ValidationResult(passed=len(errors) == 0, errors=errors)
```

**ROI**: Alto. Confianza para automatizar.

---
