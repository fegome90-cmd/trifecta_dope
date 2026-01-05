#### ast symbols (ERROR - FILE_NOT_FOUND)

```bash
$ uv run trifecta ast symbols sym://python/mod/context_service 2>&1
{
  "status": "error",
  "kind": "skeleton",
  "refs": [],
  "errors": [
    {
      "code": "FILE_NOT_FOUND",
      "message": "Could not find module for context_service",
      "details": {}
    }
  ],
  "next_actions": []
}
```

**Nota**: El comando `ast symbols` falló con FILE_NOT_FOUND. Esto indica que el SymbolResolver no pudo encontrar el módulo.

---
