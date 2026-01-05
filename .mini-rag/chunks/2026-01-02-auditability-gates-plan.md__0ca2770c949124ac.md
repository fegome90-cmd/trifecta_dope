| Área | Prueba | Tipo | Falla Esperada Hoy | Señal de Arreglo | Riesgos |
|------|--------|------|--------------------|------------------|---------|
| **Import Structure** | `uv run pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` | Unit | ImportError: `SymbolInfo` no existe | PASS: test colecta (puede fallar asserts) | **DECISIÓN: Arreglar import en test, NO re-export** |
| **Import Structure** | `uv run pytest tests/unit/test_pr2_integration.py --collect-only -q` | Unit | ImportError: `SkeletonMapBuilder` desde ast_parser | PASS: test colecta | Cambiar import a symbol_selector |
| **Import Structure** | `uv run pytest tests/unit/test_telemetry_extension.py --collect-only -q` | Unit | ImportError: `_relpath` no existe | PASS: test colecta | Remover import o reimplementar inline |
| **Path Hygiene (unit)** | `pytest tests/unit/test_path_hygiene.py -v` | Unit | Test no existe aún | PASS: sanitized_dump() funciona | Nuevo test en Blocker 1 |
| **Path Hygiene (integration)** | `uv run trifecta ctx sync -s . && rg '"/Users/' _ctx/context_pack.json; echo RC=$?` | Integration | RC=0 (matches encontrados, FAIL) | RC=1 (no matches, PASS) | **TEST TRIPWIRE CRÍTICO** |
| **Symbol Resolution** | `uv run trifecta ast symbols sym://python/mod/context_service` | Integration | FILE_NOT_FOUND (busca en cwd) | status=ok o error≠FILE_NOT_FOUND | **DECISIÓN: segment_root/src/ convención
