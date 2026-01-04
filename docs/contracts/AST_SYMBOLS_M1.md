# AST Symbols M1 Contract

## Command

```bash
trifecta ast symbols "sym://python/mod/<module.path>" --segment <path>
```

## Output Format (JSON)

### Success Response

```json
{
  "status": "ok",
  "segment_root": "/abs/path/to/segment",
  "file_rel": "src/module.py",
  "symbols": [
    {
      "kind": "function",
      "name": "foo",
      "line": 10
    },
    {
      "kind": "class",
      "name": "Bar",
      "line": 20
    }
  ]
}
```

### Error Response

```json
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for src.module"
}
```

## Stability Rules

- **Keys are stable**: Never renamed, only added
- **`symbols` is always a list**: Can be empty if file has no top-level functions/classes
- **`line` is `start_line`**: From SymbolInfo.start_line
- **Exit codes**: 0 for success, 1 for error

## Examples

### Example 1: Query existing module

```bash
$ trifecta ast symbols "sym://python/mod/src.domain.result" --segment .
{
  "status": "ok",
  "segment_root": "/path/to/project",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 5},
    {"kind": "class", "name": "Err", "line": 15}
  ]
}
```

### Example 2: Module not found

```bash
$ trifecta ast symbols "sym://python/mod/nonexistent" --segment .
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for nonexistent"
}
```
