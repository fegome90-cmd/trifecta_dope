#### 2. `ctx.get`

```python
def ctx_get(
    ids: list[str],
    mode: Literal["skeleton", "node", "window", "raw"] = "node",
    budget: int = 1200
) -> GetResult:
    """Get context with precise modes."""

    if mode == "skeleton":
        # Solo firmas
        return get_skeletons(ids)
    elif mode == "node":
        # Solo el nodo AST
        return get_ast_nodes(ids)
    elif mode == "window":
        # Nodo + N líneas alrededor
        return get_windows(ids, radius=20)
    else:
        # Texto completo (último recurso)
        return get_raw(ids)
```
