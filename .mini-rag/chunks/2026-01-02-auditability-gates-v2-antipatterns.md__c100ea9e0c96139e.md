| Área | Prueba | Tipo | Falla Esperada Hoy | Señal de Fix | Riesgos | AP Evitados |
|------|--------|------|--------------------|--------------|---------|-------------|
| **Import Structure** | `pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` | Unit | ImportError: `SymbolInfo` no existe | RC=0 (collect ok) | AP9: No re-exports, arreglar import | AP2: Determinista (fixture自有), AP9: Import correcto |
| **Import Structure** | `pytest tests/unit/test_pr2_integration.py --collect-only -q` | Unit | ImportError: `SkeletonMapBuilder` desde ast_parser | RC=0 (collect ok) | Import desde symbol_selector | AP9: Cambiar import, no re-export |
| **Import Structure** | `pytest tests/unit/test_telemetry_extension.py --collect-only -q` | Unit | ImportError: `_relpath` no existe | RC=0 (collect ok) | Reimplementar inline o agregar | AP2: Lógica simple, no dependencias |
| **Path Hygiene (unit)** | `pytest tests/unit/test_path_hygiene.py::test_sanitized_dump_no_pii -v` | Unit | Test no existe | RC=0 (asserts pass) | Validar sanitized_dump() | AP2: Fixture determinista |
| **Path Hygiene (integration)** | `pytest tests/integration/test_path_hygiene_e2e.py::test_ctx_sync_no_pii -v` | Integration | PII en context_pack.json | RC=0 (asserts pass) | Tripwire crítico: sync + validación disco | AP2: tmp_path fixture, AP3: No depende de cwd |
| **CWD Independence** | `pytest tests/integration/te
