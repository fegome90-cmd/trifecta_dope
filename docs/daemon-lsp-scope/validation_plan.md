# Plan de Validación: Subsistema Daemon + LSP

**Fecha**: 2026-03-22
**Input**: Auditoría v2 `docs/daemon-lsp-scope/technical_audit_v2.md`
**Objetivo**: Ejecutar validaciones pendientes para pasar de "cerrado localmente" a "cerrado técnicamente"

---

## Validaciones pendientes

### V1: Pytest/regresión

**Comando**: `uv run pytest`
**Objetivo**: Verificar que los cambios de código no rompieron tests existentes
**Evidencia esperada**: Exit code 0, todos los tests pasan
**Riesgo si falla**: Tests de health pueden asumir 3 checks (ahora son 2)

### V2: Health score real

**Comando**: `trifecta daemon status --repo .`
**Objetivo**: Verificar que health score es correcto sin runtime.db
**Evidencia esperada**: Health score 100% (2/2 checks) o 50% (1/2 checks)
**Riesgo si falla**: Health reporta score incorrecto

### V3: Singleton concurrente

**Comando**: Dos `trifecta daemon start --repo .` simultáneos
**Objetivo**: Verificar que solo un daemon queda vivo
**Evidencia esperada**: Segundo start falla o detecta lock
**Riesgo si falla**: Dos daemon corriendo simultáneamente

### V4: TTL

**Comando**: `TRIFECTA_DAEMON_TTL=5 trifecta daemon run`
**Objetivo**: Verificar que daemon se apaga después de 5s
**Evidencia esperada**: Daemon desaparece después de ~5s
**Riesgo si falla**: Daemon nunca se apaga por TTL

### V5: LSP envelope (requiere pyright)

**Comando**: `echo '{"method":"lsp/hover","params":{}}' | nc -U socket`
**Objetivo**: Verificar que envelope JSON funciona
**Evidencia esperada**: Responde con degraded_response o datos reales
**Riesgo si falla**: Envelope no funciona o daemon crashea
**Nota**: Requiere pyright instalado. Si no está, verificar que fallback funciona.

---

## Orden de ejecución

```
V1 (pytest) → V2 (health) → V3 (singleton) → V4 (TTL) → V5 (envelope)
```

**Dependencias**:

- V2-V4 requieren daemon corriendo (después de V1)
- V5 requiere pyright instalado (opcional)

---

## Estado después de validación

| Si todo pasa | Si algo falla |
|--------------|---------------|
| Actualizar auditoría v2 a "cerrado técnicamente" | Documentar fallo |
| Actualizar informe técnico | Decidir si corregir o aceptar riesgo |
| Declarar proyecto cerrado técnicamente | Mantener como "cerrado localmente" |
