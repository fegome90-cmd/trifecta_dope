# Guía de Uso: Sistema de Work Orders (WO)

**Versión**: 1.0  
**Fecha**: 2026-02-10  
**Estado**: Documentación operativa

---

## Arquitectura del Sistema

```
_ctx/
├── backlog/
│   └── backlog.yaml          # Epic registry (YAML only)
├── jobs/
│   ├── pending/*.yaml        # WOs esperando
│   ├── running/*.yaml        # WOs en progreso
│   ├── done/*.yaml           # WOs completados
│   └── failed/*.yaml         # WOs fallidos
└── dod/
    └── *.yaml                # Definition of Done catalog
```

**Regla Crítica**: Un WO existe en **exactamente UN** estado. Transiciones vía `mv`, nunca copiar.

---

## Estructura de un Work Order

### Campos Requeridos

```yaml
version: 1                    # Schema version
id: WO-0001                   # Pattern: ^WO-[0-9]{4}$
epic_id: E-0001               # Referencia a backlog.yaml
title: "Título descriptivo"
priority: P0                  # P0|P1|P2|P3
status: pending               # pending|running|done|failed
owner: null                   # null o identificador
scope:
  allow:                      # Lista de paths permitidos
    - "src/application/**"
    - "tests/**"
  deny:                       # Lista de paths prohibidos
    - ".env*"
    - "**/production.*"
verify:
  commands:                   # Comandos para verificar
    - "uv run pytest -q tests/unit/test_feature.py"
dod_id: DOD-DEFAULT           # Referencia a _ctx/dod/*.yaml
```

### Campos Opcionales (WO en progreso/done)

```yaml
branch: "job/WO-0001-feature" # Branch de trabajo
worktree: "../wt-WO-0001"     # Worktree path
started_at: "2026-02-10T10:00:00Z"
finished_at: "2026-02-10T14:00:00Z"
result: "success"             # success|failure
commit_sha: "abc123"          # SHA del commit
verified_at_sha: "abc123"     # SHA de verificación (nunca "HEAD")
evidence_logs:                # Evidencia de completitud
  - "_ctx/logs/WO-0001.log"
dependencies:                 # WOs que deben completarse primero
  - "WO-0001"
  - "WO-0002"

# Campos legacy (prefix x_)
x_objective: "..."
x_deliverables: []
x_notes: "..."
```

---

## Flujo de Vida de un WO

### 1. Crear WO Nuevo

```bash
# Crear archivo en pending
cat > _ctx/jobs/pending/WO-0015.yaml << 'EOF'
version: 1
id: WO-0015
epic_id: E-0001
title: "Implementar feature X"
priority: P1
status: pending
owner: null
scope:
  allow:
    - "src/domain/feature.py"
    - "tests/unit/test_feature.py"
  deny:
    - ".env*"
verify:
  commands:
    - "uv run pytest -q tests/unit/test_feature.py"
    - "uv run mypy src/domain/feature.py"
dod_id: DOD-DEFAULT
EOF

# Registrar en epic (backlog.yaml)
# Editar _ctx/backlog/backlog.yaml y agregar a wo_queue
```

### 2. Iniciar WO (pending → running)

```bash
# Mover a running (transición de estado)
mv _ctx/jobs/pending/WO-0015.yaml _ctx/jobs/running/WO-0015.yaml

# Opcional: configurar branch/worktree
cat > /tmp/patch.yaml << 'EOF'
branch: "job/WO-0015-feature"
worktree: "../wt-WO-0015"
started_at: "2026-02-10T10:00:00Z"
EOF
# Editar WO para agregar estos campos
```

### 3. Completar WO (running → done)

```bash
# Mover a done
mv _ctx/jobs/running/WO-0015.yaml _ctx/jobs/done/WO-0015.yaml

# Actualizar con evidencia
cat > /tmp/patch.yaml << 'EOF'
status: done
finished_at: "2026-02-10T14:00:00Z"
result: success
commit_sha: "a1b2c3d"        # SHA explícito, nunca "HEAD"
verified_at_sha: "a1b2c3d"
evidence_logs:
  - "_ctx/logs/WO-0015_test.log"
  - "_ctx/logs/WO-0015_build.log"
EOF
# Merge al WO
```

---

## Validación

### Validar Todo el Sistema

```bash
# Validación normal
python scripts/ctx_backlog_validate.py

# Validación estricta (falla si faltan archivos)
python scripts/ctx_backlog_validate.py --strict

# Validación con fixtures de test
python scripts/ctx_backlog_validate.py --fixtures
```

### Qué Valida

| Validación | Descripción |
|------------|-------------|
| Schema WO | Todos los campos requeridos presentes |
| Schema backlog | Epics bien formados |
| Schema DoD | Catálogo de DoDs válido |
| Referencias epic_id | WOs referencian epics existentes |
| Referencias dod_id | WOs referencian DoDs existentes |
| wo_queue | Todos los WOs en queue existen |
| scope.allow/deny | No vacíos |
| verify.commands | Al menos un comando |

### Errores Comunes

```
# WO referencia epic_id desconocido
ValueError: WO _ctx/jobs/pending/WO-0015.yaml references unknown epic_id E-9999

# WO referencia dod_id desconocido
ValueError: WO _ctx/jobs/pending/WO-0015.yaml references unknown dod_id DOD-MISSING

# WO en wo_queue no existe
ValueError: backlog.wo_queue references missing WO WO-0015

# Sin scope.allow o deny
ValueError: WO _ctx/jobs/pending/WO-0015.yaml missing scope allow/deny

# Sin verify.commands
ValueError: WO _ctx/jobs/pending/WO-0015.yaml missing verify.commands
```

---

## Estados y Transiciones

```
┌─────────┐    take     ┌─────────┐   complete   ┌───────┐
│ pending │ ───────────>│ running │ ────────────>│ done  │
└─────────┘             └─────────┘              └───────┘
                              │
                              │ fail
                              v
                         ┌─────────┐
                         │ failed  │
                         └─────────┘
```

**Comandos de Transición**:

```bash
# pending → running
mv _ctx/jobs/pending/WO-XXXX.yaml _ctx/jobs/running/WO-XXXX.yaml

# running → done
mv _ctx/jobs/running/WO-XXXX.yaml _ctx/jobs/done/WO-XXXX.yaml

# running → failed
mv _ctx/jobs/running/WO-XXXX.yaml _ctx/jobs/failed/WO-XXXX.yaml

# failed → pending (retry)
mv _ctx/jobs/failed/WO-XXXX.yaml _ctx/jobs/pending/WO-XXXX.yaml
```

---

## Patrones de Uso

### Patrón 1: Verificar Antes de Trabajar

```bash
# Siempre validar antes de modificar WOs
python scripts/ctx_backlog_validate.py --strict || exit 1

# Verificar WO específico
cat _ctx/jobs/pending/WO-0015.yaml | head -5
```

### Patrón 2: Trabajar con Scope

```bash
# Los paths en scope.allow/deny usan glob patterns
scope:
  allow:
    - "src/application/feature.py"     # Archivo específico
    - "src/domain/**"                   # Todo el directorio
    - "tests/unit/test_*.py"            # Pattern matching
  deny:
    - ".env*"                           # Ignorar secrets
    - "**/production.*"                 # No tocar producción
```

### Patrón 3: Verificación Audit-Grade

```yaml
verify:
  commands:
    # Tests específicos
    - "uv run pytest -q tests/unit/test_feature.py -v"
    # Type checking
    - "uv run mypy src/application/feature.py"
    # Linting
    - "uv run ruff check src/application/feature.py"
    # Integration tests
    - "uv run pytest -q tests/integration/test_feature_e2e.py"

# En WO done:
verified_at_sha: "abc123def"    # SHA explícito
# NUNCA:
verified_at_sha: "HEAD"         # ❌ No permitido
```

### Patrón 4: Evidencia de Completitud

```bash
# Loggear evidencia
echo "Tests passed: $(date)" > _ctx/logs/WO-0015_test.log
echo "Build success: $(date)" > _ctx/logs/WO-0015_build.log

# Referenciar en WO
evidence_logs:
  - "_ctx/logs/WO-0015_test.log"
  - "_ctx/logs/WO-0015_build.log"
```

---

## Backlog y Epics

### Estructura de backlog.yaml

```yaml
version: 1
epics:
  - id: E-0001
    title: "AST Cache Operability"
    description: |
      Descripción multi-línea del epic.
    status: complete        # complete|active|pending
    priority: P0            # P0|P1|P2|P3
    wo_queue:               # Lista ordenada de WOs
      - WO-P2.1
      - WO-P2.2
      - WO-P3.0
    x_phases:               # Metadata histórica (prefix x_)
      - name: "P0: Inventory"
        status: complete
        sha: "b0ab32f"
```

### Reglas del Backlog

1. **WOs en wo_queue deben existir**: Todo WO listado debe tener archivo correspondiente
2. **Orden significa prioridad**: WOs al inicio de wo_queue tienen mayor prioridad
3. **Estado del Epic**: Se actualiza manualmente cuando todos sus WOs están `done`
4. **Fases legacy**: Usar `x_phases` para tracking histórico

---

## Campos Legacy (Prefix x_)

```yaml
# Estos campos están permitidos pero no validados estrictamente
x_objective: "Objetivo extendido"
x_deliverables:
  - "Item 1"
  - "Item 2"
x_notes: |
  Notas libres sobre el WO
x_phases: []               # En backlog.yaml
x_legacy_wo_queue: []      # En backlog.yaml
x_curated_at: "..."        # Fecha de curación
```

---

## Integración con CLI Trifecta

### Comando ctx sync

```bash
# Sync regenera stubs basados en WOs
trifecta ctx sync --segment .

# Esto regenera:
# - repo_map.md
# - symbols_stub.md
```

### Comando load

```bash
# Cargar contexto para un WO específico
trifecta load --segment . --task "Implement WO-0015 feature X"
```

---

## Ejemplo Completo: Ciclo de Vida

```bash
#!/bin/bash
set -e

WO_ID="WO-0015"
EPIC_ID="E-0001"

# 1. VALIDAR sistema
python scripts/ctx_backlog_validate.py --strict

# 2. CREAR WO
cat > _ctx/jobs/pending/${WO_ID}.yaml << EOF
version: 1
id: ${WO_ID}
epic_id: ${EPIC_ID}
title: "Implement feature X"
priority: P1
status: pending
owner: null
scope:
  allow:
    - "src/domain/feature.py"
    - "tests/unit/test_feature.py"
  deny:
    - ".env*"
verify:
  commands:
    - "uv run pytest -q tests/unit/test_feature.py"
dod_id: DOD-DEFAULT
EOF

# 3. REGISTRAR en epic (editar backlog.yaml manualmente)
# Agregar ${WO_ID} a wo_queue

# 4. INICIAR WO
mv _ctx/jobs/pending/${WO_ID}.yaml _ctx/jobs/running/${WO_ID}.yaml

# 5. TRABAJAR (implementar feature)
# ... código ...

# 6. VERIFICAR
uv run pytest -q tests/unit/test_feature.py

# 7. COMPLETAR WO
cat > /tmp/${WO_ID}_patch.yaml << EOF
status: done
finished_at: "$(date -Iseconds)"
result: success
commit_sha: "$(git rev-parse HEAD)"
verified_at_sha: "$(git rev-parse HEAD)"
evidence_logs:
  - "_ctx/logs/${WO_ID}.log"
EOF

# Aplicar patch al WO (manual o con yq)
# mv _ctx/jobs/running/${WO_ID}.yaml _ctx/jobs/done/${WO_ID}.yaml

# 8. VALIDAR sistema final
python scripts/ctx_backlog_validate.py --strict

echo "WO ${WO_ID} completado exitosamente"
```

---

## Troubleshooting

### Error: "references unknown epic_id"

```bash
# Verificar que el epic existe
grep "id: E-0001" _ctx/backlog/backlog.yaml

# Si no existe, crear o usar epic_id correcto
```

### Error: "references unknown dod_id"

```bash
# Verificar DoDs disponibles
ls -la _ctx/dod/

# Si falta, crear o usar DOD-DEFAULT (siempre existe)
```

### Error: "missing WO in wo_queue"

```bash
# Verificar que WO existe en algún estado
find _ctx/jobs -name "WO-0015.yaml"

# Si no existe, crearlo o quitar de wo_queue
```

### WO en múltiples estados

```bash
# Error: WO duplicado
find _ctx/jobs -name "WO-0015.yaml" | wc -l
# Si > 1, eliminar duplicados manualmente

# Mantener solo el estado correcto según flujo
```

---

## Referencias

- **Schema WO**: `docs/backlog/schema/work_order.schema.json`
- **Schema backlog**: `docs/backlog/schema/backlog.schema.json`
- **Validator**: `scripts/ctx_backlog_validate.py`
- **Template**: `_ctx/jobs/template_jobs.yaml`
- **Migración**: `docs/backlog/MIGRATION.md`
- **Lecciones**: `docs/backlog/LESSONS.md`

---

*Sistema Work Orders - Trifecta Context Engine v2.0*
