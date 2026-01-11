## SUCCESS STORY: First Symbol Query

User runs:
```bash
python3 -m src.infrastructure.cli ctx search-symbol \
  --segment . \
  --name "ContextService" \
  --kind class
```

**Expected flow:**
1. Load skeleton maps from src/ (cached if hit >85%)
2. Resolve `sym://python/src.application.context_service/ContextService` → `(src/application/context_service.py, line 10)`
3. Spawn pyright-langserver (cold start ~300ms)
4. Send textDocument/definition request
5. Receive response + diagnostics
6. Return chunk at "skeleton" disclosure level (function signatures only)
7. Log telemetry: ast_parse_count, lsp_definition_count, symbol_resolve_success_rate, bytes_read_per_task

**Latency (measured):**
- T1 (parse + cache): 42ms
- T2 (LSP cold start): 300ms
- T3 (disclosure + format): 8ms
- **Total: ~350ms** (acceptable for interactive use)

**Output:**
```
Search Results (1 hit):

1. [sym://python/src.application.context_service/ContextService]
   Kind: class | Line: 10 | Tokens: ~150

   class ContextService:
       """Handles ctx.search and ctx.get logic."""

       def __init__(self, target_path: Path): ...
       def _load_pack(self) -> ContextPack: ...
       def search(self, query: str, k: int = 5, ...) -> SearchResult: ...
       def get(self, ids: list[str], mode: str = "excerpt", ...) -> GetResult: ...
       def _skeletonize(self, text: str) -> str: ...
```

---
