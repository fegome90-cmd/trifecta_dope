#### Contenido Clave:
- **Líneas 7-30**: [Tabla de Hallazgos](#a-hallazgos-evidencia-verificada) - 8 problemas con evidencia archivo:línea
  - PATH HYGIENE VIOLATION (línea 11) - `/Users/...` en context_pack.json
  - pytest ImportError (línea 12) - 3 tests rotos
  - SymbolInfo no existe (línea 13) - Bloquea tests PR2

- **Líneas 49-55**: [Dictamen](#c-dictamen)
  ```
  AUDITABLE-PARTIAL-PASS
  - Sistema core funciona (PD L0, telemetría)
  - 3 BLOCKERS críticos
  - NO hay rotación de datos
  ```

- **Líneas 62-119**: [Plan Mínimo - 3 Bloqueadores](#d-plan-mínimo-patches-must-fix)
  - **Bloqueador #1** (líneas 64-88): Sanitizar rutas absolutas
    - Archivos: `use_cases.py`, `test_path_hygiene.py`
    - DoD: No `/Users/` en pack
    - Test: `grep -E '"/Users/|"/home/' _ctx/context_pack.json`

  - **Bloqueador #2** (líneas 90-107): pytest ImportError
    - Archivos: `stubs.py`, tests
    - DoD: pytest corre sin errors
    - Test: `uv run pytest -q`

  - **Bloqueador #3** (líneas 109-119): ast symbols FILE_NOT_FOUND
    - Archivos: `symbol_selector.py`, `cli_ast.py`
    - DoD: `trifecta ast symbols` funciona
    - Test: `uv run trifecta ast symbols sym://python/mod/context_service`

- **Líneas 123-150**: [Evidencia Requerida](#e-evidencia-requerida-outputs-crudos)
  - Outputs crudos que el usuario debe pegar para cerrar PASS
