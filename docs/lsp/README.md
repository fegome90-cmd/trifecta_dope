# Análisis de Problemas del Daemon LSP

**Fecha**: 2026-01-05  
**Metodología**: Superpowers Systematic Debugging  
**Estado**: 5 problemas documentados

---

## Índice de Problemas

### 🔴 Prioridad ALTA

1. **[Duplicación LSP Clients](problema-01-duplicacion-lsp-clients.md)** (5-6h)
   - LSPClient vs LSPManager duplican 90% del código
   - Confusión arquitectural, dificulta mantenimiento
   - Solución: Migrar a LSPClient único

2. **[Race Condition en Shutdown](problema-02-race-condition-shutdown.md)** (3.5-5.5h)
   - Thread shutdown con timeout 1s puede causar stream leaks
   - Defensive programming (leak vs crash)
   - Solución: Escalating timeouts + telemetry

### 🟡 Prioridad MEDIA

3. **[Daemon TTL No Renovable](problema-03-daemon-ttl-no-renovable.md)** (3.5h)
   - TTL fijo de 180s, se reinicia daemon innecesariamente
   - Sesiones largas pierden conexión
   - Solución: Método `ping()` para keep-alive

### 🟢 Prioridad BAJA

4. **[Telemetría con Paths Inseguros](problema-04-telemetria-paths-inseguros.md)** (3h)
   - `relative_to()` falla con paths externos
   - Potencial leak de PII (usernames)
   - Solución: Helper de sanitización

5. **[Falta de Observabilidad](problema-05-falta-observabilidad.md)** (3.5h)
   - Sin métricas de daemon (uptime, requests, TTL)
   - Dificulta debugging operacional
   - Solución: Endpoint `stats` + CLI command

---

## Resumen Ejecutivo

**Total estimado**: 18.5-21h de implementación

**Hallazgos Clave**:
- Arquitectura tiene duplicación por evolución histórica
- Defensive programming bien implementado (comentarios claros)
- TTL pattern necesita modernización
- Telemetría básica necesita hardening
- Observabilidad ausente

**Recomendación**: Priorizar #1 y #2 (alta), luego #3 (media), finalmente #4 y #5 (baja/nice-to-have).

---

## Metodología

Cada problema fue investigado con **Superpowers Systematic Debugging**:

1. **Phase 1**: Root Cause Investigation (código, líneas, evidencia)
2. **Phase 2**: Pattern Analysis (comparación con soluciones conocidas)
3. **Phase 3**: Hypothesis and Testing (tests de validación)
4. **Phase 4**: Implementation (steps detallados, timeline)

---

## Archivos Analizados

### Infraestructura LSP
- [lsp_daemon.py](../../src/infrastructure/lsp_daemon.py) - Daemon server/client
- [lsp_client.py](../../src/infrastructure/lsp_client.py) - LSP client con state machine
- [daemon_paths.py](../../src/infrastructure/daemon_paths.py) - Path utilities

### Aplicación
- [lsp_manager.py](../../src/application/lsp_manager.py) - Duplicado (legacy)
- [pr2_context_searcher.py](../../src/application/pr2_context_searcher.py) - Usa LSPManager
- [ast_parser.py](../../src/application/ast_parser.py) - Cache AST

### Tests
- [test_lsp_client_strict.py](../../tests/unit/test_lsp_client_strict.py)
- [test_lsp_daemon.py](../../tests/integration/test_lsp_daemon.py)
- [test_ast_lsp_pr2.py](../../tests/unit/test_ast_lsp_pr2.py)

---

## Próximos Pasos

**Para el agente implementador**:

1. Leer documento de arquitectura: [daemon-architecture-analysis.md](daemon-architecture-analysis.md)
2. Elegir problema a implementar (recomendado: #1 primero)
3. Seguir implementation steps en cada problema
4. Ejecutar tests de validación
5. Verificar con `make test-gates`

**Comandos útiles**:
```bash
# Buscar todos los usos de LSPManager
rg "LSPManager" --type py

# Ejecutar tests del daemon
uv run pytest tests/integration/test_lsp_daemon.py -v

# Verificar imports
uv run trifecta ast symbols sym://python/mod/src.infrastructure.lsp_daemon
```

---

**Investigador**: GitHub Copilot  
**Superpowers Skill**: systematic-debugging  
**Workspace**: /workspaces/trifecta_dope
