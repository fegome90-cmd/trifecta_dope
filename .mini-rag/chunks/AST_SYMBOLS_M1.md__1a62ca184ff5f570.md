### Example 2: Module not found

```bash
$ trifecta ast symbols "sym://python/mod/nonexistent" --segment .
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for nonexistent"
}
```
