# Problema 5: Falta de Observabilidad del Daemon

**Prioridad**: 🟢 BAJA | **Estimado**: 3.5h | **Fecha**: 2026-01-05

---

## Problema

Daemon no expone métricas: no sabemos uptime, TTL restante, requests procesados, estado LSP. Dificulta debugging en producción.

**Ubicación**: [lsp_daemon.py:24-176](../../src/infrastructure/lsp_daemon.py#L24-L176) - sin método `get_stats()`

---

## Solución

Agregar endpoint `stats` al protocolo daemon + CLI command:
- ✅ Método `get_stats()` → JSON con métricas
- ✅ Protocol handler para `method: "stats"`
- ✅ CLI: `trifecta daemon stats`

**Ejemplo Output**:
```
🟢 Daemon Status: Running
  Uptime: 2h 34m 12s
  TTL Remaining: 156s
  Requests: 847
```

---

## Documentos Complementarios

- **Análisis detallado**: [problema-05-analisis.md](problema-05-analisis.md)
- **Implementación**: [problema-05-implementacion.md](problema-05-implementacion.md)
- **CLI design**: [problema-05-cli.md](problema-05-cli.md)

---

## Timeline

- Stats endpoint: 1h
- CLI commands: 1.5h
- Tests: 1h
- **Total: 3.5h**
