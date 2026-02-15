---
segment: trifecta_dope
profile: load_only
---

# Prime Trifecta_Dope - Lista de Lectura

> **REPO_ROOT**: `/Users/felipe_gonzalez/Developer/agent_h`
> Todas las rutas son relativas a esta raiz.
>
> **PRIME CONTRACT**:
> Prime contiene SOLO paths (1 línea por path) ordenados por prioridad.
> Prohibido incluir chunks, texto largo o comentarios inline.
> 1 línea = 1 Path Autoritativo.

## [HIGH] Prioridad ALTA - Fundamentos

**Leer primero para entender el contexto del segmento.**

1. `trifecta_dope/src/infrastructure/lsp_daemon.py`
2. `trifecta_dope/src/infrastructure/cli.py`
3. `trifecta_dope/src/infrastructure/lsp_client.py`
4. `trifecta_dope/src/infrastructure/telemetry.py`
5. `trifecta_dope/tests/integration/test_lsp_daemon.py`
6. `trifecta_dope/src/application/use_cases.py`
7. `trifecta_dope/src/domain/ast_models.py`
8. `trifecta_dope/.github/copilot-instructions.md`
9. `trifecta_dope/src/infrastructure/cli_ast.py`
10. `trifecta_dope/README.md`
11. `trifecta_dope/src/cli/error_cards.py`
12. `trifecta_dope/tests/acceptance/test_ctx_sync_preconditions.py`
13. `trifecta_dope/src/domain/naming.py`
14. `trifecta_dope/src/infrastructure/daemon_paths.py`
15. `trifecta_dope/src/application/context_service.py`
16. `trifecta_dope/src/application/search_get_usecases.py`
17. `trifecta_dope/src/application/telemetry_pr2.py`


## [MED] Prioridad MEDIA - Implementación

**Leer para entender bugs recientes y testing.**

1. `trifecta_dope/docs/bugs/create_cwd_bug.md`
2. `trifecta_dope/tests/integration/test_lsp_telemetry.py`
3. `trifecta_dope/src/application/telemetry_reports.py`
4. `trifecta_dope/tests/integration/test_daemon_paths_constraints.py`

## [LOW] Prioridad BAJA - Referencias

<!-- Documentacion de referencia, archivada -->
<!-- Ejemplos: API docs, especificaciones -->

## [MAP] Mapa Mental

```mermaid
mindmap
  root(trifecta_dope)
    <!-- Agregar conceptos clave del segmento -->
    <!-- Ejemplo:
    Fundamentos
    Arquitectura
    Componentes
    Interfaces
    -->
```

## [DICT] Glosario

| Término | Definición |
|---------|------------|
| **LSP Daemon** | Servidor LSP persistente con UNIX socket IPC, 180s TTL |
| **Error Card** | Sistema de errores estructurados con códigos estables (TRIFECTA_ERROR_CODE) |
| **Context Pack** | Archivo JSON con chunks de documentación indexados |
| **Segment** | Directorio de proyecto con `_ctx/` y configuración Trifecta |
| **Prime File** | `_ctx/prime_{segment_id}.md` - Lista de lectura prioritizada |
| **Dogfooding** | Testing real del CLI usando workflows completos (create→refresh-prime→sync) |

## [NOTE] Notas

- **Fecha ultima actualizacion**:
- **Mantenedor**: <!-- Agregar si aplica -->
- **Ver tambien**: [skill.md](../skill.md) | [agent.md](./agent.md)
