### 2.5 Presupuesto de Tokens (Backpressure)

**Ubicación**: `src/application/context_service.py:111-223`

```python
def get(
    self,
    ids: list[str],
    mode: Literal["raw", "excerpt", "skeleton"] = "raw",
    budget_token_est: Optional[int] = None,
    max_chunks: Optional[int] = None,
    stop_on_evidence: bool = False,
    query: Optional[str] = None,
) -> GetResult:
```

**Comportamiento**:
- Default budget: 1200 tokens
- Si un chunk excede el presupuesto en modo `raw`, se reduce a 20 líneas
- Se deja de procesar IDs cuando se alcanza el presupuesto
- `stop_reason`: `"complete"`, `"budget"`, `"max_chunks"`, `"evidence"`

---
