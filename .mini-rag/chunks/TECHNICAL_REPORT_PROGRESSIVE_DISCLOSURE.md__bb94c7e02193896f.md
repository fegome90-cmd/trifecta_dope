### 5.2 Ejemplo Completo de Uso

```bash
# 1. Sincronizar contexto
$ uv run trifecta ctx sync -s .
🔄 Running build...
✅ Build complete. Validating...
✅ Validation Passed
🔄 Regenerating stubs...
   ✅ Regenerated: repo_map.md, symbols_stub.md

# 2. Buscar chunks relevantes
$ uv run trifecta ctx search -s . -q "telemetry"
Search Results (3 hits):
1. [skill:abc123] telemetry.md
   Score: 1.00 | Tokens: ~450
2. [prime:def456] prime_telemetry.md
   Score: 0.75 | Tokens: ~200

# 3. Obtener L0 skeleton
$ uv run trifecta ctx get -s . -i "skill:abc123" --mode skeleton
Selected Chunks (1):
1. [skill:abc123] telemetry.md
   ## Overview
   ## Usage
   def record_event():
   def flush():
   ...
Total Tokens: ~45

# 4. Obtener L1 hover info
$ uv run trifecta ast hover src/infrastructure/telemetry.py -l 42 -c 10
{
  "status": "ok",
  "kind": "skeleton",
  "data": {
    "uri": "src/infrastructure/telemetry.py",
    "range": {"start_line": 42, "end_line": 52},
    "children": []
  }
}
```

---
