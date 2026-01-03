#### 3. `ctx.diagnostics`

```python
def ctx_diagnostics(
    scope: Literal["hot", "project"] = "hot"
) -> list[Diagnostic]:
    """Get active diagnostics from LSP."""

    if scope == "hot":
        files = hotset_files
    else:
        files = all_project_files

    return lsp.diagnostics(files)
```
