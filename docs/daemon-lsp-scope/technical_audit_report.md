# Auditoría Técnica: Fases 1-5 — Subsistema Daemon + LSP

**Fecha**: 2026-03-22
**Rol**: Auditor técnico disciplinado
**Input**: Informe técnico `docs/daemon-lsp-scope/technical_report_phases_1_5.md`
**Metodología**: Contraste de claims contra evidencia real del repo

---

## 1. Veredicto

### Veredicto honesto (corregido)

| Componente | Claim del informe | Evidencia real | Veredicto corrección |
|------------|-------------------|----------------|----------------------|
| Daemon start/stop/status/restart | OPERATIVO LOCAL | ✅ Código existe, CLI funciona | CERRADO LOCALMENTE |
| PING/HEALTH/SHUTDOWN | OPERATIVO LOCAL | ✅ Código existe, responde correctamente | CERRADO LOCALMENTE |
| LSP via envelope JSON | OPERATIVO LOCAL | ⚠️ Código existe, pero LSPClient.request() puede fallar si backend no instalado | CERRADO LOCALMENTE (con fallback) |
| Singleton concurrente | OPERATIVO LOCAL | ⚠️ Código existe, pero no hay test de concurrencia | CERRADO LOCALMENTE (sin validación) |
| TTL con LSP activo | OPERATIVO LOCAL | ⚠️ Código existe, pero no hay test de TTL + LSP | CERRADO LOCALMENTE (sin validación) |
| LSP con backend real | OPERATIVO LOCAL | ❌ No hay pyright/pylsp instalado, nunca probado con backend real | NO VALIDADO |
| Telemetry events | OPERATIVO LOCAL | ✅ Código emite events, pero no hay test de que llegan a events.jsonl | CERRADO LOCALMENTE |
| Pytest/regresión | CERRADO TÉCNICAMENTE | ❌ No se ejecutó pytest después de los cambios | NO CERRADO TÉCNICAMENTE |

### Overdeclaration detectada

El informe técnico declara "OPERATIVO LOCAL" para funcionalidades que:

- Nunca fueron probadas con backend real (LSP)
- Nunca fueron testeado con pytest (regresión)
- Nunca fueron validadas con concurrencia (singleton)

**Corrección**: El veredicto correcto es "CERRADO LOCALMENTE" para lo que fue observado funcionando, y "NO VALIDADO" para lo que requiere tests o backend.

---

## 2. Qué está sólido

Solo hechos observados directamente:

1. **Daemon start funciona**: `trifecta daemon start --repo .` crea socket y PID. Observado.
2. **Daemon status funciona**: `trifecta daemon status --repo .` lee PID y socket. Observado.
3. **PING responde**: `echo "PING" | nc -U socket` devuelve `PONG`. Observado.
4. **HEALTH responde**: Devuelve JSON con pid, uptime, version, protocol, lsp state. Observado.
5. **SHUTDOWN funciona**: Devuelve `OK` y proceso termina. Observado.
6. **Código existe para**: singleton locking, TTL, LSPClient, envelope JSON, telemetry.
7. **Tests existen para**: DaemonManager, daemon_paths, lsp_client, lsp_daemon (tests que ya pasaban antes de los cambios).
8. **Comentarios de autoridad correctos**: LSPManager = DEPRECATED, LSPDaemonServer = REFERENCE.

---

## 3. Qué está blando/riesgoso/contradictorio

### Contradicciones internas del informe

| # | Contradicción | Evidencia |
|---|---------------|-----------|
| 1 | Informe dice "LSP: OPERATIVO LOCAL" pero también dice "LSP real data: pyright/pylsp no instalado → fallback explícito" | technical_report_phases_1_5.md sección 7 |
| 2 | Informe dice "singleton funciona" pero sección "Lo que NO fue testeado" dice "Concurrent daemon start con singleton: No hay test de concurrencia" | technical_report_phases_1_5.md sección 7-8 |
| 3 | Informe dice "Tests existentes y pasan" pero no se ejecutó `uv run pytest` después de los cambios | No hay evidencia de ejecución de tests |
| 4 | Informe dice "health check score 0/50/100" pero no verificó que el score real sea 50/100 con daemon corriendo | No hay evidencia de ejecución de `trifecta daemon status` |
| 5 | Informe dice "LSP envelope JSON funciona" pero no hay evidencia de que un envelope fue enviado y procesado | No hay log de ejecución de echo JSON | nc -U socket |

### Claims sin evidencia suficiente

| Claim | Problema |
|-------|----------|
| "LSPClient integrado correctamente" | No se probó con pyright instalado. Solo se verificó que el código no crashea al importar. |
| "Singleton funciona" | No se probó con dos starts simultáneos. Solo se verificó que el código no crashea. |
| "TTL funciona" | No se probó con `TRIFECTA_DAEMON_TTL=10 daemon run` y verificación de que se apaga. |
| "Telemetry funciona" | No se verificó que events.jsonl reciba los eventos. |
| "Health check 0/50/100" | No se verificó ejecutando `trifecta daemon status` después de eliminar runtime.db check. |

---

## 4. Ajustes concretos

### Ajustes al informe técnico

| Sección | Cambio | Razón |
|---------|--------|-------|
| Resumen ejecutivo | Cambiar "OPERATIVO LOCAL" a "CERRADO LOCALMENTE" | No hay suficiente evidencia para "operativo" |
| Sección 7 tabla "Lo que FUNCIONA" | Agregar columna "Evidencia" con fuente de cada claim | Transparencia |
| Sección 7 tabla "Lo que NO fue testeado" | Expandir a lista completa de validaciones pendientes | Honestidad |
| Sección 8 Riesgos | Mover "Tests de health pueden fallar" a riesgo #1 | Es el riesgo más inmediato |
| Sección 9 Próximos pasos | Priorizar "Verificar tests pasan" como paso #0 | Es prerequisito para todo lo demás |

### Ajustes al estado del proyecto

| Capability | Estado actual (informe) | Estado corregido (auditoría) |
|------------|------------------------|------------------------------|
| Daemon start/stop/restart | OPERATIVO LOCAL | CERRADO LOCALMENTE |
| PING/HEALTH/SHUTDOWN | OPERATIVO LOCAL | CERRADO LOCALMENTE |
| LSP via envelope | OPERATIVO LOCAL | CERRADO LOCALMENTE (sin backend real) |
| Singleton | OPERATIVO LOCAL | CERRADO LOCALMENTE (sin validación concurrente) |
| TTL | OPERATIVO LOCAL | CERRADO LOCALMENTE (sin validación) |
| LSP con backend real | NO VALIDADO | NO VALIDADO |
| Pytest/regresión | CERRADO TÉCNICAMENTE | NO EJECUTADO |
| Telemetry events | OPERATIVO LOCAL | CERRADO LOCALMENTE (sin verificación) |

---

## 5. Siguiente paso recomendado

**Validación inmediata** antes de declarar cualquier cosa más allá de "cerrado localmente":

1. Ejecutar `uv run pytest` para verificar que no hay regresiones
2. Ejecutar `trifecta daemon status --repo .` para verificar health score real
3. Ejecutar `echo '{"method":"lsp/hover","params":{}}' | nc -U socket` para verificar envelope
4. Ejecutar dos `daemon start` simultáneos para verificar singleton
5. Ejecutar `TRIFECTA_DAEMON_TTL=5 daemon run` y verificar que se apaga

**Solo después de esta validación** se puede declarar "cerrado técnicamente".

---

## 6. Prompt para el siguiente agente

```
Tarea: Ejecutar validación de claims del informe técnico Fases 1-5.

Contexto: Auditoría técnica identificó que el informe sobredeclara madurez.
Ver informe de auditoría: docs/daemon-lsp-scope/technical_audit_report.md

Validaciones pendientes:
1. Ejecutar `uv run pytest` — verificar que tests pasan con los cambios
2. Ejecutar `trifecta daemon status --repo .` — verificar health score real
3. Ejecutar `echo '{"method":"lsp/hover","params":{}}' | nc -U socket` — verificar envelope
4. Ejecutar dos `daemon start` simultáneos — verificar singleton
5. Ejecutar `TRIFECTA_DAEMON_TTL=5 daemon run` — verificar TTL

Reglas:
- No implementar nuevas capacidades
- Solo validar lo que ya existe
- Reportar resultados honestos
- Si algo falla, documentar el fallo
- Actualizar informe técnico con resultados reales
