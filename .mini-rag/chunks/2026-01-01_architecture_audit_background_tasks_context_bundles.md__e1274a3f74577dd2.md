### A.2 UseCase → Tool Call Logging

**Archivo**: `src/application/search_get_usecases.py`

**Punto de inserción**: Dentro de `SearchUseCase.execute`, después de `service.search()`.

```python
# search_get_usecases.py

def execute(self, target_path, query, limit):
    result = service.search(term, k=limit * 2)

    # NUEVO: Log tool call to bundle
    if self.bundle_recorder:
        self.bundle_recorder.log_tool_call(
            name="ctx.search",
            args={"query": query, "limit": limit},
            result={"hits": len(result.hits)},
            timing_ms=elapsed_ms
        )

    # ... rest of formatting
```

---
