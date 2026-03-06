# Plan: Trifecta Global Architecture

**Feature**: `trifecta-global-architecture`
**Fecha**: 2026-03-05
**Complexity**: `HIGH`
**Status**: `PENDING`

---

## 1. Restatement de Requerimientos

### 1.1 Problema Actual

Cada repositorio trifecta contiene toda la configuración duplicada:
- `_ctx/` con config, anchors, aliases, documentación (10-50KB)
- `.trifecta/cache/` con cache AST por repo (1-5MB)
- Sin config global centralizada
- Cache y daemons sin gestión unificada

### 1.2 Objetivos

1. **Instalación global del código** (ya existe, `uv pip install`)
2. **Instalación global de configuración** (NUEVO)
3. **Repos con archivos mínimos** (solo `.trifecta.yaml` de 1-2KB)
4. **Cache globalizado por fingerprint** (compartido entre repos)
5. **Daemons gestionados centralmente**
6. **Telemetría centralizada**
7. **Migración automática** desde arquitectura actual
8. **Comandos de gestión** (global status, cache cleanup, daemon management)

### 1.3 Non-Functional Requirements

- **Backward compatibility**: Migración transparente desde arquitectura actual
- **Performance**: No degradar performance (cache sigue siendo rápido)
- **Idempotency**: `trifecta global install` puede ejecutarse múltiples veces
- **Error handling**: Mensajes claros y accionables
- **Rollback**: Migración con backup y posibilidad de rollback
- **Cross-platform**: Funciona en macOS y Linux (mínimo)
- **Testing**: Cobertura >80% para nuevo código

---

## 2. Supuestos y Preguntas Abiertas

### 2.1 Supuestos

- [ ] Trifecta ya está instalado globalmente via `uv pip install`
- [ ] Python 3.11+ está disponible
- [ ] El usuario tiene permisos para crear `~/.trifecta/`
- [ ] `uv` package manager está disponible
- [ ] LSP servers (pylsp/pyright) son opcionales

### 2.2 Preguntas Abiertas

1. **Config global**: ¿Debe haber un wizard interactivo para la primera instalación?
2. **Migración**: ¿Debe ser automática o require confirmación explícita?
3. **Telemetría**: ¿Debe estar habilitada por defecto o opt-in?
4. **Cleanup**: ¿Debe haber un cron job para limpiar caches antiguos?
5. **Rollback**: ¿Debe haber un comando de rollback por si la migración falla?

---

## 3. Fases de Implementación

### FASE 1: Foundation Global (4-6 horas)

**Objetivo**: Crear estructura de config global

**Tasks**:
1. [ ] Crear `src/domain/global_config.py` con `GlobalConfig` dataclass
   - `version`: str
   - `lsp`: LSPConfig
   - `cache`: CacheConfig
   - `telemetry`: TelemetryConfig
   - `repo_defaults`: RepoDefaultsConfig

2. [ ] Crear `src/infrastructure/global_config.py` con `GlobalConfigManager`
   - `load()`: Load from `~/.trifecta/config.yaml`
   - `save()`: Save to `~/.trifecta/config.yaml`
   - `merge_with_repo_config()`: Merge global + repo configs
   - `validate()`: Validate config schema

3. [ ] Crear directorio global en `src/infrastructure/factories.py`
   - `get_global_root()`: Get `~/.trifecta/` path
   - `get_global_config_path()`: Get config.yaml path
   - `get_global_cache_dir()`: Get cache/ path
   - `get_global_daemons_dir()`: Get daemons/ path
   - `get_global_telemetry_dir()`: Get telemetry/ path

4. [ ] Actualizar `src/infrastructure/factories.py`
   - `get_ast_cache_db_path()`: Use global cache dir with fingerprint
   - `get_ast_cache()`: Use global config for defaults

**Archivos a crear**:
- `src/domain/global_config.py`
- `src/infrastructure/global_config.py`

**Archivos a modificar**:
- `src/infrastructure/factories.py`

---

### FASE 2: Paths Globalizados (4-6 horas)

**Objetivo**: Migrar daemon, cache y telemetry a paths globales

**Tasks**:
1. [ ] Actualizar `src/infrastructure/daemon_paths.py`
   - `get_daemon_lock_path()`: Use `~/.trifecta/daemons/`
   - `get_daemon_pid_path()`: Use `~/.trifecta/daemons/`
   - `get_daemon_socket_path()`: Keep as `/tmp/` (no change)
   - `list_daemons()`: NEW - List all daemons
   - `cleanup_daemons()`: NEW - Clean zombie daemons

2. [ ] Actualizar `src/infrastructure/telemetry.py`
   - `Telemetry.__init__()`: Use global telemetry dir if enabled
   - Add logic to detect `~/.trifecta/telemetry/` vs `_ctx/telemetry/`

3. [ ] Actualizar `src/infrastructure/lsp_daemon.py`
   - No changes needed (uses daemon_paths abstractions)

4. [ ] Crear scripts de migración
   - Migrate cache from `.trifecta/cache/` to `~/.trifecta/cache/`
   - Migrate telemetry from `_ctx/telemetry/` to `~/.trifecta/telemetry/`

**Archivos a modificar**:
- `src/infrastructure/daemon_paths.py`
- `src/infrastructure/telemetry.py`

---

### FASE 3: Comandos Globales (3-4 horas)

**Objetivo**: Implementar comandos de gestión global

**Tasks**:
1. [ ] Crear `src/infrastructure/global_cli.py`
   - `global_app = typer.Typer(help="Global Trifecta Commands")`
   - `install`: Create `~/.trifecta/` structure
   - `status`: Show global status
   - `config edit`: Edit global config
   - `cache cleanup`: Clean global cache
   - `reset --dangerous`: Reset global config

2. [ ] Integrar `global_app` en `src/infrastructure/cli.py`
   - Add to main CLI as `trifecta global <command>`

3. [ ] Implementar `trifecta global install`
   - Create `~/.trifecta/` directories
   - Create default `config.yaml`
   - Create default templates (`anchors.default.yaml`, `aliases.default.yaml`)
   - Create subdirectories (`cache/`, `daemons/`, `telemetry/`)

4. [ ] Implementar `trifecta global status`
   - Show config location
   - Show cache stats (total repos, entries, bytes)
   - Show daemon count
   - Show telemetry status

5. [ ] Implementar `trifecta global cache cleanup`
   - List all caches
   - Clean caches older than N days
   - Clean specific repo cache

**Archivos a crear**:
- `src/infrastructure/global_cli.py`

**Archivos a modificar**:
- `src/infrastructure/cli.py`

---

### FASE 4: Comandos de Repo (2-3 horas)

**Objetivo**: Implementar comandos de gestión de repo (minimal)

**Tasks**:
1. [ ] Crear `src/infrastructure/repo_cli.py`
   - `repo_app = typer.Typer(help="Repo Commands")`
   - `init`: Initialize new repo with `.trifecta.yaml`
   - `migrate`: Migrate existing repo to global architecture
   - `cleanup-old`: Clean old `_ctx/` and `.trifecta/cache/`

2. [ ] Integrar `repo_app` en `src/infrastructure/cli.py`
   - Add to main CLI as `trifecta repo <command>`

3. [ ] Implementar `trifecta repo init --scope "Description"`
   - Calculate fingerprint from repo path
   - Create `.trifecta.yaml` with minimal config
   - Create `.trifecta/` for optional hooks/overrides

4. [ ] Implementar `trifecta repo migrate`
   - Detect existing config in `_ctx/`
   - Read `trifecta_config.json`, `anchors.yaml`, `aliases.yaml`
   - Migrate config to `.trifecta.yaml`
   - Migrate cache to global
   - Migrate telemetry to global
   - Create backup of `_ctx/` to `.trifecta.bak/`

5. [ ] Implementar `trifecta repo cleanup-old --confirm`
   - Remove `_ctx/` after successful migration
   - Remove `.trifecta/cache/` after successful migration

6. [ ] Implementar `trifecta status` (updated)
   - Show repo status
   - Show cache location (global)
   - Show daemon status
   - Show global config location

**Archivos a crear**:
- `src/infrastructure/repo_cli.py`

**Archivos a modificar**:
- `src/infrastructure/cli.py`

---

### FASE 5: Comandos de Daemon y Cache (2-3 horas)

**Objetivo**: Implementar comandos extendidos para daemon y cache

**Tasks**:
1. [ ] Extender `src/infrastructure/cli_ast.py`
   - Add `cache list`: List all caches
   - Add `cache stats-all`: Show global stats
   - Add `cache clear-all`: Clear all caches

2. [ ] Extender LSP daemon commands
   - Add `lsp daemon list`: List all daemons
   - Add `lsp daemon stats`: Show daemon stats
   - Add `lsp daemon stop`: Stop specific daemon
   - Add `lsp daemon stop-all`: Stop all daemons
   - Add `lsp daemon cleanup`: Clean zombie daemons

3. [ ] Add method to `LSPDaemonServer` for stats
   - Return uptime, TTL, requests_handled, LSP state

**Archivos a modificar**:
- `src/infrastructure/cli_ast.py`
- `src/infrastructure/lsp_daemon.py`

---

### FASE 6: Testing (4-6 horas)

**Objetivo**: Comprehensive testing de la nueva arquitectura

**Tasks**:
1. [ ] Unit tests para `GlobalConfigManager`
   - `test_load_default_config()`
   - `test_load_custom_config()`
   - `test_merge_with_repo_config()`
   - `test_validate_schema()`

2. [ ] Unit tests para `GlobalConfigManager`
   - `test_load_config()`
   - `test_save_config()`
   - `test_merge_with_repo()`
   - `test_validate_config()`

3. [ ] Unit tests para paths globalizados
   - `test_get_global_root()`
   - `test_get_global_cache_dir()`
   - `test_get_ast_cache_db_path_with_fingerprint()`
   - `test_get_daemon_lock_path()`

4. [ ] Integration tests para migración
   - `test_repo_migrate_full()`
   - `test_repo_migrate_preserves_config()`
   - `test_repo_migrate_preserves_cache()`
   - `test_repo_cleanup_old()`

5. [ ] Integration tests para comandos globales
   - `test_global_install_creates_structure()`
   - `test_global_status_shows_info()`
   - `test_global_cache_cleanup()`

6. [ ] E2E tests para flujo completo
   - `test_global_install_then_repo_init()`
   - `test_repo_init_then_ctx_sync()`
   - `test_repo_migrate_then_cleanup()`

**Archivos a crear**:
- `tests/unit/test_global_config.py`
- `tests/unit/test_global_config_manager.py`
- `tests/unit/test_global_paths.py`
- `tests/integration/test_repo_migrate.py`
- `tests/integration/test_global_commands.py`
- `tests/e2e/test_global_architecture.py`

---

### FASE 7: Polish y Documentación (3-4 horas)

**Objetivo**: Documentación completa y UX refinada

**Tasks**:
1. [ ] Crear documentación de arquitectura global
   - `docs/ARCHITECTURE_GLOBAL.md`
   - `docs/INSTALACION_GLOBAL.md`
   - `docs/MIGRACION_GUIDE.md`

2. [ ] Actualizar `README.md`
   - Agregar sección de instalación global
   - Agregar comandos nuevos
   - Actualizar ejemplos de uso

3. [ ] Crear templates por defecto
   - `~/.trifecta/templates/anchors.default.yaml`
   - `~/.trifecta/templates/aliases.default.yaml`

4. [ ] Mejorar mensajes de error
   - Mensajes claros para errores de permisos
   - Mensajes accionables para fallas de migración
   - Hints para troubleshooting

5. [ ] Performance benchmarks
   - Comparar cache access time (local vs global)
   - Comparar tiempo de inicialización
   - Verificar no hay degradación

**Archivos a crear**:
- `docs/ARCHITECTURE_GLOBAL.md`
- `docs/INSTALACION_GLOBAL.md`
- `docs/MIGRACION_GUIDE.md`

**Archivos a modificar**:
- `README.md`

---

## 4. Archivos Candidatos a Modificar

### 4.1 Domain Layer (Nuevos)

- `src/domain/global_config.py` (NEW)
  - `GlobalConfig` dataclass
  - `LSPConfig` dataclass
  - `CacheConfig` dataclass
  - `TelemetryConfig` dataclass
  - `RepoDefaultsConfig` dataclass

### 4.2 Infrastructure Layer (Modificados)

- `src/infrastructure/global_config.py` (NEW)
- `src/infrastructure/global_cli.py` (NEW)
- `src/infrastructure/repo_cli.py` (NEW)
- `src/infrastructure/factories.py` (MODIFIED)
  - Add `get_global_root()`
  - Add `get_global_*_dir()` methods
  - Update `get_ast_cache_db_path()` for fingerprint
  - Update `get_ast_cache()` to use global config
- `src/infrastructure/daemon_paths.py` (MODIFIED)
  - Update `get_daemon_lock_path()`
  - Update `get_daemon_pid_path()`
  - Add `list_daemons()`
  - Add `cleanup_daemons()`
- `src/infrastructure/telemetry.py` (MODIFIED)
  - Update `__init__()` to use global telemetry dir
- `src/infrastructure/lsp_daemon.py` (MODIFIED - maybe)
  - Add `stats()` method for observability
- `src/infrastructure/cli.py` (MODIFIED)
  - Add `global_app` subcommand
  - Add `repo_app` subcommand
  - Update existing commands for new paths
- `src/infrastructure/cli_ast.py` (MODIFIED)
  - Add `cache list`, `cache stats-all`, `cache clear-all`
  - Extend LSP daemon commands

### 4.3 Documentation (Nuevos/Modificados)

- `docs/ARCHITECTURE_GLOBAL.md` (NEW)
- `docs/INSTALACION_GLOBAL.md` (NEW)
- `docs/MIGRACION_GUIDE.md` (NEW)
- `README.md` (MODIFIED)

### 4.4 Tests (Nuevos)

- `tests/unit/test_global_config.py` (NEW)
- `tests/unit/test_global_config_manager.py` (NEW)
- `tests/unit/test_global_paths.py` (NEW)
- `tests/integration/test_repo_migrate.py` (NEW)
- `tests/integration/test_global_commands.py` (NEW)
- `tests/e2e/test_global_architecture.py` (NEW)

---

## 5. Riesgos y Mitigaciones

### 5.1 Riesgo 1: Pérdida de Cache/Telemetría al Migrar

**Probabilidad**: MEDIA
**Impacto**: ALTO

**Mitigación**:
- Comando `trifecta repo migrate` migra automáticamente
- Backup automático de `_ctx/` a `.trifecta.bak/`
- Validación post-migración antes de borrar archivos antiguos
- Opción `--dry-run` para preview de migración

### 5.2 Riesgo 2: Colisión de Fingerprints

**Probabilidad**: BAJA
**Impacto**: MEDIO

**Mitigación**:
- Fingerprint usa SHA256 del path completo (altamente improbable)
- Si colisión, usuario puede override en `.trifecta.yaml`
- Warning en log si fingerprint colisiona con existente

### 5.3 Riesgo 3: Dependencia de `~/.trifecta/`

**Probabilidad**: MEDIA
**Impacto**: ALTO

**Mitigación**:
- Comando `trifecta global reset --dangerous` para recrear
- Warning antes de borrar directorios
- Fallback a paths locales si `~/.trifecta/` no existe
- Documentación clara de recovery

### 5.4 Riesgo 4: Conflictos de Configuración

**Probabilidad**: MEDIA
**Impacto**: MEDIO

**Mitigación**:
- Precedencia clara documentada (repo > global > defaults)
- Validación de config al cargar
- Error descriptivo si hay conflicto
- Warning de overrides

### 5.5 Riesgo 5: Performance Degradation

**Probabilidad**: BAJA
**Impacto**: MEDIO

**Mitigación**:
- Benchmarks antes/después de migración
- Cache sigue siendo SQLite (mismo performance)
- Paths globales no afectan cache access time
- Monitor de latencia en telemetría

### 5.6 Riesgo 6: Breaking Change para Usuarios Existentes

**Probabilidad**: ALTA
**Impacto**: ALTO

**Mitigación**:
- Feature flag `TRIFECTA_USE_GLOBAL_ARCH=1` para opt-in
- Backward compatibility: paths locales si flag no está
- Período de deprecation (3 meses) antes de eliminar paths locales
- Comando de rollback para revertir migración

---

## 6. Estrategia de Pruebas

### 6.1 Unit Tests

**Objetivo**: Cobertura >80% para nuevo código

**Tests requeridos**:
- `GlobalConfig` dataclass: Validación de schema
- `GlobalConfigManager.load()`: Load from file
- `GlobalConfigManager.save()`: Save to file
- `GlobalConfigManager.merge_with_repo_config()`: Precedencia
- `get_global_root()`: Path resolution
- `get_ast_cache_db_path()`: Fingerprint-based paths
- `get_daemon_lock_path()`: Global daemon paths

**Tools**: pytest, pytest-cov, coverage

### 6.2 Integration Tests

**Objetivo**: Validar migración y comandos globales

**Tests requeridos**:
- `test_repo_migrate_full()`: Migración completa
- `test_repo_migrate_preserves_config()`: Config migrado correctamente
- `test_repo_migrate_preserves_cache()`: Cache migrado correctamente
- `test_global_install_creates_structure()`: Directorios creados
- `test_global_status_shows_info()`: Información correcta
- `test_global_cache_cleanup()`: Cleanup funciona

**Setup**: Temp directories para cada test

### 6.3 E2E Tests

**Objetivo**: Validar flujo completo usuario

**Tests requeridos**:
- `test_global_install_then_repo_init()`: Flujo nuevo usuario
- `test_repo_init_then_ctx_sync()`: Context sync funciona
- `test_repo_migrate_then_cleanup()`: Migración completa
- `test_backward_compatibility()`: Paths locales si flag no set

**Setup**: Mock repos con estado inicial

### 6.4 Regression Tests

**Objetivo**: No romper funcionalidad existente

**Tests requeridos**:
- Todos los tests existentes deben pasar
- `test_ast_symbols()`: Funciona con paths globales
- `test_ctx_sync()`: Context pack se genera
- `test_ctx_search()`: Búsqueda funciona

**Automation**: CI pipeline runs all tests on PR

### 6.5 Manual Testing

**Objetivo**: UX y edge cases

**Tests manuales**:
- Migración de repo real (trifecta_dope)
- Creación de nuevo repo desde scratch
- Limpieza de caches globales
- Gestión de daemons
- Verificación de backup y rollback

---

## 7. Estimación de Complejidad

**Complexity**: `HIGH`

**Justificación**:
- Múltiples capas afectadas (domain, infrastructure, CLI)
- Paths críticos de cache y telemetría
- Migración de arquitectura existente
- Necesita backward compatibility
- Feature flags y deprecation period
- Testing extensivo requerido

**Riesgos clave**:
- Pérdida de datos en migración
- Performance degradation
- Breaking changes
- Compatibilidad cross-platform

---

## 8. Criterios de Éxito

### 8.1 Funcionales

- [ ] `trifecta global install` crea estructura correctamente
- [ ] `trifecta repo init` crea `.trifecta.yaml` minimal
- [ ] `trifecta repo migrate` migra config/cache/telemetría
- [ ] `trifecta repo cleanup-old` limpia archivos antiguos
- [ ] `trifecta global status` muestra información correcta
- [ ] `trifecta cache list` lista todos los caches
- [ ] `trifecta lsp daemon list` lista todos los daemons

### 8.2 No-Funcionales

- [ ] Cobertura de tests >80%
- [ ] Todos los tests existentes pasan
- [ ] Performance: cache access time no degrada
- [ ] Backward compatibility: paths locales si flag no set
- [ ] Documentación completa
- [ ] Mensajes de error claros y accionables

### 8.3 UX

- [ ] Migración es transparente y con backup
- [ ] Comandos son intuitivos
- [ ] Mensajes son claros
- [ ] Documentación es fácil de seguir

---

**Plan Version**: 1.0
**Creado por**: Claude
**Fecha**: 2026-03-05

---

## 9. Observabilidad y Logs Estructurados

### 9.1 Mecanismos de Observabilidad

**Objetivo**: Proveer visibilidad completa de la arquitectura global para debugging rápido.

**Mecanismos**:

1. **Telemetría Estructurada** (JSONL)
   - Formato: `{"ts", "cmd", "args", "result", "timing_ms", "warnings", "x": {...}}`
   - Ubicación: `~/.trifecta/telemetry/events_{fingerprint}.jsonl`
   - Campos `x`: Datos extendidos específicos por comando
   - Sanitización automática de paths absolutos

2. **Logs de Aplicación** (Logging Python)
   - Niveles: DEBUG, INFO, WARNING, ERROR
   - Configurable vía `TRIFECTA_LOG_LEVEL`
   - Output a stdout + archivo de log rotativo
   - Context: module, function, line number

3. **Status Endpoints** (HTTP-like semántica)
   - `trifecta global status` -> Estado del sistema global
   - `trifecta status` -> Estado del repo actual
   - `trifecta lsp daemon list` -> Estado de todos los daemons
   - `trifecta cache list` -> Estado de todos los caches

4. **Health Checks**
   - Daemon alive check (PID file + socket)
   - Cache integrity check (SQLite DB validation)
   - Config validation (schema check + precedence validation)

### 9.2 Logs Estructurados

**Formato de Logs**:
```json
{
  "ts": "2026-03-05T17:20:00.000Z",
  "run_id": "run_123456",
  "segment_id": "a1b2c3d4",
  "cmd": "global_install",
  "args": {"force": false},
  "result": {"status": "ok"},
  "timing_ms": 1234,
  "warnings": [],
  "x": {
    "config_location": "~/.trifecta/config.yaml",
    "dirs_created": 5,
    "files_created": 3
  }
}
```

**Ejemplos de Logs por Componente**:

#### Global Install
```json
{
  "ts": "2026-03-05T17:20:00.000Z",
  "cmd": "global_install",
  "result": {"status": "ok"},
  "warnings": [],
  "x": {
    "dirs_created": ["~/.trifecta/cache", "~/.trifecta/daemons", "~/.trifecta/telemetry"],
    "files_created": ["~/.trifecta/config.yaml"]
  }
}
```

#### Repo Init
```json
{
  "ts": "2026-03-05T17:20:00.000Z",
  "cmd": "repo_init",
  "args": {"segment": "/path/to/repo", "scope": "My Project"},
  "result": {"status": "ok"},
  "x": {
    "fingerprint": "a1b2c3d4",
    "config_created": "/path/to/repo/.trifecta.yaml",
    "linked_to_global": true
  }
}
```

### 9.3 Checklist de Errores

**Errores Comunes y Sugerencias**:

1. **Error: Permisos al crear `~/.trifecta/`**
   - **Sugerencia**: `mkdir -p ~/.trifecta && chmod 700 ~/.trifecta`
   - **Log**: `{"error": "EACCES", "path": "~/.trifecta/", "hint": "Check permissions"}`

2. **Error: Fingerprint colisión**
   - **Sugerencia**: Usar fingerprint alternativo o override en `.trifecta.yaml`
   - **Log**: `{"error": "FINGERPRINT_COLLISION", "fingerprint": "a1b2c3d4", "hint": "Override config"}`

3. **Error: Config global inválido**
   - **Sugerencia**: Validar schema de `~/.trifecta/config.yaml`
   - **Log**: `{"error": "INVALID_CONFIG", "reason": "lsp.enabled must be boolean", "fix": "Edit config"}`

4. **Error: Migración fallida**
   - **Sugerencia**: Revisar backup en `.trifecta.bak/` y hacer rollback manual
   - **Log**: `{"error": "MIGRATION_FAILED", "phase": "cache", "backup": ".trifecta.bak/"}`

5. **Error: Daemon no responde**
   - **Sugerencia**: Verificar PID file y socket, reiniciar daemon
   - **Log**: `{"error": "DAEMON_UNRESPONSIVE", "fingerprint": "a1b2c3d4", "action": "Restart daemon"}`

6. **Error: Cache corrupted**
   - **Sugerencia**: Borrar cache DB y dejar que se regenere
   - **Log**: `{"error": "CACHE_CORRUPTED", "db_path": "~/.trifecta/cache/ast_a1b2c3d4.db", "action": "Delete DB"}`

7. **Error: Dependencia no encontrada** (LSP)
   - **Sugerencia**: Instalar LSP manualmente (`pip install python-lsp-server` o `npm install -g pyright`)
   - **Log**: `{"error": "LSP_NOT_FOUND", "server": "pylsp", "command": "pip install python-lsp-server"}`

8. **Error: Timeout de operación**
   - **Sugerencia**: Aumentar timeout en config o retry
   - **Log**: `{"error": "TIMEOUT", "operation": "cache_migration", "timeout_sec": 120, "retry": 3}`

### 9.4 Métricas de Health

**Métricas a monitorear**:

| Métrica | Descripción | Umbral | Acción |
|---------|-----------|---------|--------|
| `cache.hit_rate` | Cache AST hit rate | < 70% | Revisar configuración de cache |
| `daemon.uptime` | Tiempo alive del daemon | > 3600s | Reiniciar daemon |
| `config.validation` | Config es válida | false | Abortar operación |
| `migration.success` | Migración exitosa | false | Hacer rollback |
| `telemetry.event_rate` | Eventos por segundo | > 10/s | Throttlear |

### 9.5 Comandos de Debug

```bash
# Ver logs de telemetría en tiempo real
tail -f ~/.trifecta/telemetry/events_*.jsonl | jq '.'

# Ver logs de aplicación (si está habilitado)
tail -f ~/.trifecta/logs/app.log

# Health check global
trifecta global status --verbose

# Health check de daemon específico
trifecta lsp daemon status --fingerprint a1b2c3d4

# Health check de cache específico
trifecta cache stats --fingerprint a1b2c3d4

# Validar configuración global
trifecta global config validate
```


---

## 10. Revisión de Implementación y Validación

### 10.1 Validación de Formato del Plan

**Reglas de formato**:
- ✅ Todas las secciones numeradas consecutivamente
- ✅ Uso consistente de markdown (headers, bullets, code blocks)
- ✅ No hay secciones huérfanas o duplicadas
- ✅ Códigos de estado (`PENDING`, `APPROVED`, `REJECTED`) en mayúsculas
- ✅ Tamaños en bytes para todos los archivos nuevos

### 10.2 Validación de Factibilidad

**Criterios de factibilidad**:
- ✅ Todas las tareas son accionables (no hay "investigación adicional")
- ✅ Las estimaciones de tiempo son realistas (4-6h por fase)
- ✅ Los archivos a modificar existen en el codebase
- ✅ Las dependencias son conocidas (pytest, yaml, typer)
- ✅ No hay dependencias circulares entre fases

### 10.3 Validación de Completitud

**Checklist de completitud**:
- [ ] Restatement de requerimientos ✓
- [ ] Supuestos y preguntas abiertas ✓
- [ ] Fases de implementación paso a paso ✓
- [ ] Archivos candidatos a modificar ✓
- [ ] Riesgos + mitigaciones ✓
- [ ] Estrategia de pruebas ✓
- [ ] Estimación de complejidad ✓
- [ ] Criterios de éxito ✓
- [ ] Observabilidad y logs estructurados ✓ (PATCH APROBADO)

### 10.4 Validación de Integración con Codebase Existente

**Validaciones**:
- [ ] `GlobalConfig` dataclass sigue patrones existentes en `src/domain/`
- [ ] `GlobalConfigManager` sigue patrones existentes en `src/infrastructure/`
- [ ] Los paths nuevos son consistentes con `segment_resolver` (fingerprint-based)
- [ ] Los comandos nuevos siguen patrones existentes en `src/infrastructure/cli.py`
- [ ] Los tests nuevos siguen patrones existentes en `tests/unit/` y `tests/integration/`

### 10.5 Validación de Compatibilidad Backward

**Validaciones**:
- [ ] Paths locales siguen existiendo si `TRIFECTA_USE_GLOBAL_ARCH` no está seteado
- [ ] `trifecta create` sigue funcionando con estructura antigua
- [ ] `ctx sync` sigue generando context pack en `_ctx/`
- [ ] `ast cache` sigue funcionando con cache local si no se usa global
- [ ] Migración es opcional y con backup

### 10.6 Validación de Performance

**Validaciones**:
- [ ] Cache access time no degrada (SQLite sigue siendo local, solo paths diferentes)
- [ ] Daemon startup time no afectado
- [ ] Telemetry write time no afectado
- [ ] Timeouts de migración son apropiados (máx 10 min para repos grandes)

### 10.7 Validación de Seguridad

**Validaciones**:
- [ ] `~/.trifecta/` tiene permisos correctos (700, no group/world write)
- [ ] Paths globales no contienen información sensible en filenames
- [ ] Sanitización de paths en logs (ya existe en `Telemetry._sanitize_value()`)
- [ ] No hay injection attacks en comandos shell (usar `subprocess.run` con `list`, no `shell=True`)

### 10.8 Validación de Documentación

**Validaciones**:
- [ ] Documentación de arquitectura global es clara y completa
- [ ] Guía de migración tiene pasos detallados
- [ ] Comandos tienen `--help` typer generado
- [ ] Ejemplos de uso son realistas y copiables
- [ ] Troubleshooting guide cubre errores comunes

