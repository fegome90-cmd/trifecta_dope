# E-V1 Runtime Maturity Plan (Post-Foundation)

## Metadata

- **Status**: APPROVED FOR EXECUTION
- **Created**: 2026-03-06
- **Scope**: Runtime maturity hardening (NOT foundation rework)
- **Lote recomendado**: WO-M0 + WO-M1 + WO-M2

---

## 1. Resumen Ejecutivo

**Problema actual**: El foundation de E-V1 está cerrado, pero el código de daemon tiene un bug bloqueante: `daemon_manager.py` llama a `subprocess.Popen(["python", "-m", "trifecta", "daemon", "run"])` que **no existe**. El comando `trifecta daemon run` devuelve error. Esto invalida cualquier test E2E de daemon.

**Diferencia con foundation**: Foundation validó arquitectura y contratos. Runtime maturity valida comportamiento operativo bajo condiciones reales (daemon lifecycle real, identidad de repo robusta, operación multi-repo básica).

**Estrategia**: Characterization-first hardening. Primero fix del bug bloqueante, luego hardening de identidad (paths), luego validación de operación global (multi-repo). SQLite contention se caracteriza pero no se sobreingenia. DB version queda como infra preventiva de baja prioridad.

---

## 2. Priorización

| Área | Impacto | Riesgo actual | Esfuerzo | Dependencias reales | Prioridad |
|------|---------|---------------|----------|---------------------|-----------|
| **Daemon run command** | CRITICAL | Bug real: start() llama a comando inexistente | LOW | Ninguna | **P0** |
| **Path canonicalization** | HIGH | Duplicate registration por symlink/relativo no detectado | LOW | Ninguna | **P1** |
| **Cross-repo smoke** | MEDIUM | Diseño lo soporta, sin evidencia de operación global | LOW | Ninguna | **P2** |
| **SQLite contention** | MEDIUM | Comportamiento bajo contención no caracterizado | MEDIUM | Ninguna | **P2** |
| **DB version marker** | LOW | No hay usuarios, infra preventiva | LOW | Ninguna | **P3** |

**Justificación**:

- **P0 Daemon run**: BUG REAL. El código existe pero está roto. `daemon_manager.py:50` llama a comando inexistente.
- **P1 Path**: Alto impacto, bajo esfuerzo. Duplicate registration es bug real en uso normal.
- **P2 Cross-repo**: Si el sistema se llama "global", debe haber evidencia mínima de operación multi-repo.
- **P2 SQLite**: Medio impacto. Caracterizar comportamiento, harden solo si hace falta.
- **P3 DB version**: Infra preventiva. No hay usuarios aún, puede esperar.

**Paralelización**: P1, P2 (cross-repo), P3 no dependen de P0 ni entre sí. P2 (SQLite) tampoco tiene dependencias.

---

## 3. Secuencia Recomendada

### Wave 1: Bug crítico (secuencial, bloqueante)
- **WO-M0**: Implementar `trifecta daemon run` (P0)

**Por qué primero**: Bug real que invalida daemon E2E.

### Wave 2: Hardening de identidad + validación global (paralelo)
- **WO-M1**: Path canonicalization (P1)
- **WO-M2**: Cross-repo smoke (P2)

**Por qué paralelo**: No hay dependencias entre ellas. Juntas cierran el ciclo: identidad robusta + operación global básica.

### Wave 3: Characterization + infra preventiva (paralelo, puede esperar)
- **WO-M4**: SQLite contention characterization (P2)
- **WO-M3**: DB version marker (P3)

**Por qué después**: No bloquean operación básica. Pueden ejecutarse en paralelo si hay capacidad.

---

## 4. Work Orders Propuestos

| WO | Título | Objetivo | Alcance | No incluye | Criterio de aceptación |
|----|--------|----------|---------|------------|------------------------|
| **WO-M0** | Daemon run command | Hacer que daemon start funcione | Implementar `trifecta daemon run` que escuche en socket y responda a health check. **Mínimo loop de proceso necesario para start/status/stop reales y testeables.** | Daemon pooling, load balancing, protocolo complejo, semi-plataforma features | `daemon start` → `daemon status` muestra running=true y el PID corresponde a un proceso vivo verificable por el sistema operativo |
| **WO-M1** | Path canonicalization | Prevenir duplicate registration | Resolver symlinks, normalizar `..`, detectar equivalencia relativo/absoluto | Unicode normalization, case sensitivity por OS | `/tmp/repo`, symlink a `/tmp/repo`, `../tmp/repo` producen mismo repo_id; intento de registro duplicado falla con error: "repo already registered at <canonical_path>" |
| **WO-M2** | Cross-repo smoke | Validar operación multi-repo básica | Registrar 3 repos, verificar list/show/status aislados sin cruzar metadata | Daemon aislado por repo, operaciones concurrentes | `repo-list` devuelve exactamente 3; `repo-show <id>` resuelve cada uno sin cruzar metadata; `status --repo <path>` devuelve identidad correcta por repo; no hay colisión de IDs |
| **WO-M3** | DB version marker | Infra preventiva para schema evolution | Agregar `schema_version` table con version=1, fail-closed si mismatch | Migration runner, auto-migration | DB nueva tiene version=1; DB sin version falla con mensaje "schema version mismatch: expected 1, got none" |
| **WO-M4** | SQLite contention characterization | Caracterizar comportamiento bajo contención, harden mínimo necesario | Test de N writers concurrentes contra **DB en disco**, documentar comportamiento observado, implementar hardening mínimo necesario si se requiere | Connection pooling complejo, distributed locking | N writers concurrentes contra DB en disco terminan sin corrupción; estado final consistente; **política de contención documentada y verificada**: (A) contención rechazada con error explícito, o (B) contención absorbida con serialización interna |

---

## 5. Estrategia de Testing

| Área | Tipo de prueba mínimo | Evidencia mínima requerida | Futuro endurecimiento |
|------|----------------------|---------------------------|----------------------|
| **Daemon run** | E2E (proceso real) | start→status→stop con socket real, PID verificable por OS | Crash recovery, socket cleanup tras kill -9 |
| **Path canonicalization** | Unit (path equivalence) | symlink, `..`, relativo/absoluto producen mismo repo_id; duplicate rechazado con error explícito | Case sensitivity por OS, Unicode normalization |
| **Cross-repo** | Smoke (multi-repo básico) | 3 repos, list devuelve 3, show por id funciona sin cruzar metadata | Daemon aislado por repo, operaciones concurrentes |
| **DB version** | Integration (version check) | DB nueva tiene version=1, DB sin version falla con error explícito | Migration 1→2 con runner simple |
| **SQLite contention** | Integration (concurrent on-disk) | N writers contra **DB en disco**, sin corrupción, estado final consistente, política de contención verificada | Stress test largo, fault injection |

**Proceso real requerido para**:
- Daemon E2E (socket/PID/signal son OS-level)

**DB en disco requerido para**:
- SQLite contention (file locking es kernel-level, `:memory:` no sirve)

**Basta con integration/smoke para**:
- Path canonicalization
- Cross-repo
- DB version

---

## 6. Riesgos y Tradeoffs

### Qué pasa si abordamos esto mal

| Escenario | Consecuencia |
|-----------|--------------|
| Implementar WAL/pooling sin characterization | Over-engineering, complejidad innecesaria |
| Daemon run con protocolo complejo o semi-plataforma | Scope creep, retrasa todo |
| `:memory:` para tests de contención | Falsa confianza, file locking no se prueba |
| Migration runner completo | Solución buscando problema |

### Dónde NO vale la pena sobreingenierizar

| Área | Límite |
|------|--------|
| Daemon run | Comando simple que escucha socket y responde ping. **Mínimo loop para start/status/stop.** No pooling, no load balancing, no semi-plataforma. |
| SQLite | Si characterization muestra que SQLite default maneja bien N writers, no agregar WAL. |
| Migration | Solo version marker + fail-closed. No auto-migration. |
| Path | Canonicalización básica con `resolve()`. No Unicode normalization. |

### Qué SÍ necesita comportamiento real

| Área | Por qué |
|------|---------|
| Daemon E2E | Socket creation, PID management, signal handling son OS-level |
| SQLite contention | File locking es kernel-level, no se puede mockear confiablemente |

### Qué se puede resolver con contratos + fail-closed

| Área | Enfoque |
|------|--------|
| DB version | Si schema_version mismatch → error explícito, no auto-migrate |
| Path duplicates | Si canonical path ya existe → rechazar con error explícito, no merge |
| SQLite contention | Política explícita: (A) error en contención, o (B) serialización interna. Verificar que se cumple. |

### Qué dejar deliberadamente fuera

| Área | Razón |
|------|-------|
| Migration runner | No hay historia de migraciones reales |
| Case sensitivity | OS-dependent, complejidad alta para beneficio bajo |
| Unicode normalization | Caso extremadamente raro en repos |
| Daemon pooling | Prematuro sin carga real |
| Daemon semi-plataforma | Scope creep, mantener mínimo |

---

## 7. Dependencias Técnicas Mínimas

| Dependencia | WO que la necesita | Estado |
|-------------|-------------------|--------|
| Socket server simple (stdlib) | WO-M0 | `socket` module disponible |
| `signal` module (stdlib) | WO-M0 | Disponible |
| `/tmp` fixture + cleanup | WO-M1, WO-M2, WO-M4 | Ya disponible en tests |
| `os.symlink` (stdlib) | WO-M1 | Disponible |
| `concurrent.futures` (stdlib) | WO-M4 | Disponible |
| **Temporary on-disk SQLite DB** | WO-M4 | Requiere fixture nuevo |
| Multi-process/thread harness | WO-M4 | `concurrent.futures` + tempfile |
| `os.kill(pid, 0)` para verificación de PID | WO-M0 tests | Disponible en Unix-like |

**No se necesitan dependencias externas nuevas.**

---

## 8. Definición de Éxito

El runtime pasó de "foundation-only" a "operationally hardened in key paths" si:

- [ ] **C1**: `trifecta daemon start` ejecuta sin error, `daemon status` muestra running=true y el PID corresponde a un proceso vivo verificable por el sistema operativo
- [ ] **C2**: Paths equivalentes (symlink, `..`, relativo/absoluto) producen mismo repo_id; intento de duplicate registration falla con error explícito que incluye canonical path
- [ ] **C3**: 3 repos registrados, `repo-list` devuelve exactamente 3, `repo-show` por id funciona sin cruzar metadata, `status --repo <path>` devuelve identidad correcta por repo, no hay colisión de IDs
- [ ] **C4**: DB nueva incluye schema_version=1, DB sin version falla con mensaje "schema version mismatch: expected 1, got none"
- [ ] **C5**: N writers concurrentes contra DB en disco terminan sin corrupción; estado final consistente; política de contención documentada y verificada

**Frase auditable**:
> "The E-V1 runtime handles real daemon lifecycle, canonical repository identity for duplicate detection, and basic multi-repo global operations at smoke level. SQLite contention characterization and schema version fail-closed hardening remain for the next maturity wave."

---

## 9. Recomendación Final

### Lote mínimo recomendado para próxima iteración

**WO-M0 + WO-M1 + WO-M2** (Opción B)

**Por qué**:
- WO-M0 es BUG REAL BLOQUEANTE (P0)
- WO-M1 es alto impacto, bajo esfuerzo (P1)
- WO-M2 valida el claim "global" con bajo esfuerzo (P2)
- Juntos cierran el ciclo: daemon real + identidad robusta + operación global básica

### Qué dejar deliberadamente fuera

- **WO-M4 (SQLite contention)**: Caracterización primero. Puede ejecutarse en paralelo si hay capacidad.
- **WO-M3 (DB version)**: Infra preventiva, no hay usuarios.
- **Case sensitivity / Unicode**: Complejidad alta, beneficio bajo.
- **Daemon pooling / semi-plataforma**: Prematuro, scope creep.

### Frase exacta al terminar

> **E-V1 runtime now supports real daemon lifecycle, canonical repository identity for duplicate detection, and basic multi-repo global operations at smoke level. SQLite contention characterization and schema version fail-closed hardening remain for the next maturity wave.**

---

## 10. Notas de Implementación

### WO-M0 Consideraciones

- **No convertir en semi-plataforma**: Solo el mínimo loop necesario para start/status/stop reales
- Socket simple, no pooling
- Health check básico (ping/pong)
- PID management con cleanup apropiado
- Signal handling mínimo (SIGTERM para graceful shutdown)

### WO-M4 Política de Contención

Antes de implementar, definir explícitamente:
- **Opción A**: Contención rechazada con error explícito al usuario
- **Opción B**: Contención absorbida con serialización interna (SQLite default)

La elección debe documentarse y el test debe verificar que la política se cumple.
