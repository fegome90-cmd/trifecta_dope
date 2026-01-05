### Step 3: Write minimal implementation

Modify `src/application/symbol_selector.py:91-116`:

```python
def resolve(self, query: SymbolQuery) -> Result[Candidate, ASTError]:
    # Convert Python module path (dots) to filesystem path (slashes)
    path_as_dir = query.path.replace(".", "/")

    # Simple resolution logic
    candidate_file = self.root / f"{path_as_dir}.py"
    candidate_init = self.root / path_as_dir / "__init__.py"

    file_exists = candidate_file.exists() and candidate_file.is_file()
    init_exists = candidate_init.exists() and candidate_init.is_file()

    if file_exists and init_exists:
        return Err(
            ASTError(code=ASTErrorCode.AMBIGUOUS_SYMBOL, message="Ambiguous module path")
        )

    if file_exists:
        return Ok(Candidate(f"{path_as_dir}.py", "mod"))
    elif init_exists:
        return Ok(Candidate(f"{path_as_dir}/__init__.py", "mod"))

    return Err(
        ASTError(
            code=ASTErrorCode.FILE_NOT_FOUND, message=f"Could not find module for {query.path}"
        )
    )
```
