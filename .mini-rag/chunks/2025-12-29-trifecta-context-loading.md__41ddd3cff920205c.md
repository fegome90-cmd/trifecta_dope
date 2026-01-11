### Tool 2: `ctx.get`

**Propósito**: Obtener chunks específicos

```python
def ctx_get(
    segment: str,
    ids: list[str],
    mode: Literal["raw", "excerpt", "skeleton"] = "raw",
    budget_token_est: Optional[int] = None
) -> GetResult:
    """
    Obtiene chunks por ID con control de presupuesto.

    Modes:
        - raw: Texto completo
        - excerpt: Primeras N líneas
        - skeleton: Solo headings + primera línea

    Returns:
        {
            "chunks": [
                {
                    "id": "skill-core-rules-abc123",
                    "text": "...",
                    "token_est": 150
                }
            ],
            "total_tokens": 450
        }
    """
```
