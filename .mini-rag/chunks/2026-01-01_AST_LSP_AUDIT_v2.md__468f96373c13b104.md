### 2. Selector v0 (Symbol Router)

**Format:** `sym://python/{module}/{qualified_name}`

Examples:
```
sym://python/src.application.context_service/ContextService
sym://python/src.infrastructure.cli/search
sym://python/src.domain.models/TrifectaConfig.segment
```

**Resolver Logic:**
1. Parse symbol query → extract module + name
2. Load skeleton map for module
3. Find definition in skeleton (functions/classes list)
4. Return: (file_path, start_line, kind)
5. **Fail-closed**: If ambiguous (2+ matches), return all + require user disambiguation

**Single-Writer Contract:**
- Only ContextService.search() may resolve symbols
- All symbol queries → same resolver instance (no concurrent mutations)
- Lock: Session file mutex (see prerequisite)

---
