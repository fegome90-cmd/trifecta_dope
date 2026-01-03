# Informe de Optimización: Trifecta Docs (skill.md + agent.md + prime.md)

## Resumen Ejecutivo

**Objetivo**: Eliminar duplicación, mejorar separación de concerns, reducir skill.md bajo 100 líneas.

**Estado Actual**:

- `skill.md`: 97 líneas (cerca del límite de 100)
- `agent_trifecta_dope.md`: 113 líneas
- `prime_trifecta_dope.md`: 67 líneas
- **Total**: 277 líneas

**Propuesta**:

- `skill.md`: 75 líneas (-22, -23%) ✅
- `agent_trifecta_dope.md`: 133 líneas (+20, +18%)
- `prime_trifecta_dope.md`: 85 líneas (+18, +27%)
- **Total**: 293 líneas (+16, pero mejor organizado)

---

## Duplicaciones Detectadas

### 1. Resources (On-Demand) - CRÍTICO

**Ubicación**: skill.md L90-93 + agent.md L100-104

**Contenido duplicado**:

```markdown
- `@_ctx/prime_trifecta_dope.md` - Lista de lectura obligatoria
- `@_ctx/agent.md` - Stack técnico y gates
- `@_ctx/session_trifecta_dope.md` - Log de handoffs (runtime)
```

**Solución**:

- ❌ ELIMINAR de agent.md (redundante)
- ✅ MANTENER en skill.md (es el punto de entrada)

**Ahorro**: 5 líneas en agent.md

---

### 2. REPO_ROOT - MENOR

**Ubicación**:

- prime.md L8: `/Users/felipe_gonzalez/Developer/agent_h`
- agent.md frontmatter L4: `repo_root: /Users/felipe_gonzalez/Developer/agent_h`
- skill.md L8: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/`

**Análisis**: No es duplicación real, cada uno tiene propósito:

- prime.md: Define root para paths relativos
- agent.md: Metadata YAML
- skill.md: Ubicación del segmento

**Acción**: Ninguna (correcto como está)

---

### 3. Comandos Trifecta - DISPERSIÓN

**Ubicación**:

- skill.md L29-50: Protocolo completo con comandos
- agent.md L78: Solo `trifecta ctx validate` en Gates

**Problema**: Comandos detallados en skill.md (debería ser en agent.md)

**Solución**: Ver sección "Reorganización de Contenido"

---

## Inconsistencias Detectadas

### 1. Source of Truth (agent.md L13-20)

**Problema**: Lista archivos que deberían estar en prime.md

**Contenido**:

```
| Reglas de Sesión | [skill.md](../skill.md) |
| Dependencias | `pyproject.toml` |
| Lógica Core | `src/domain/` y `src/application/` |
```

**Solución**:

- Mantener tabla en agent.md (es metadata útil)
- Agregar estos paths a prime.md [HIGH]

---

### 2. Secciones Vacías en prime.md

**Problema**:

- [MED] Prioridad MEDIA: vacío
- [LOW] Prioridad BAJA: vacío
- [MAP] Mapa Mental: vacío
- [DICT] Glosario: vacío

**Solución**: Llenar con contenido relevante (ver propuesta detallada)

---

## Reorganización de Contenido

### skill.md: De 97 → 75 líneas

#### ELIMINAR (22 líneas)

1. **L90-93: Resources (On-Demand)** → Duplicado en agent.md

   ```diff
   - ## Resources (On-Demand)
   - - `@_ctx/prime_trifecta_dope.md` - Lista de lectura obligatoria
   - - `@_ctx/agent.md` - Stack técnico y gates
   - - `@_ctx/session_trifecta_dope.md` - Log de handoffs (runtime)
   ```

2. **L52-56: STALE FAIL-CLOSED PROTOCOL** → Mover a agent.md

   ```diff
   - STALE FAIL-CLOSED PROTOCOL (CRITICAL):
   - - Si `ctx validate` falla o `stale_detected=true` -> STOP inmediatamente
   - - Ejecutar: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
   - - Registrar en session.md: "Stale: true -> sync+validate executed"
   - - Prohibido continuar hasta PASS
   ```

3. **L29-50: CRITICAL PROTOCOL** → Simplificar (reducir de 22 a 8 líneas)

   ```diff
   - ### CRITICAL PROTOCOL: Session Evidence Persistence (Trifecta)
   -
   - Antes de ejecutar cualquier herramienta (Trifecta CLI o agentes externos), DEBES seguir este orden. NO tomes atajos.
   -
   - 1) PERSISTE intencion minima (CLI proactivo - NO depende del LLM):
   - ```bash
   - trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   - ```
   - [... 18 líneas más ...]

   + ### Session Evidence Protocol
   +
   + 1. **Persist**: `trifecta session append --segment . --summary "<task>"`
   + 2. **Sync**: `trifecta ctx sync --segment .`
   + 3. **Execute**: `ctx search` → `ctx get`
   + 4. **Record**: `trifecta session append --segment . --summary "Completed <task>"`
   +
   + > Ver [agent.md](./_ctx/agent_trifecta_dope.md) para comandos completos y protocolos detallados.
   ```

**Total eliminado/simplificado**: 22 líneas

#### MANTENER

- Onboarding (L10-17): 8 líneas
- Core Rules (L19-23): 5 líneas
- When to Use (L65-69): 5 líneas
- Core Pattern (L71-76): 6 líneas
- Session Persistence (L78-81): 4 líneas
- Common Mistakes (L83-88): 6 líneas

**Nuevo total**: ~75 líneas ✅

---

### agent.md: De 113 → 133 líneas

#### AGREGAR nueva sección "Protocols" (después de L51)

```markdown
## Protocols

### Session Evidence Persistence

**Orden obligatorio** (NO tomes atajos):

1. **Persist Intent**:
   ```bash
   trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   ```

1. **Sync Context**:

   ```bash
   trifecta ctx sync --segment .
   ```

2. **Verify Registration** (confirma que se escribió en session.md)

3. **Execute Context Cycle**:

   ```bash
   trifecta ctx search --segment . --query "<tema>" --limit 6
   trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
   ```

4. **Record Result**:

   ```bash
   trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
   ```

### STALE FAIL-CLOSED Protocol

**CRITICAL**: Si `ctx validate` falla o `stale_detected=true`:

1. **STOP** inmediatamente
2. **Execute**:

   ```bash
   trifecta ctx sync --segment .
   trifecta ctx validate --segment .
   ```

3. **Record** en session.md: `"Stale: true -> sync+validate executed"`
4. **Prohibido** continuar hasta PASS

**Prohibiciones**:

- YAML de historial largo
- Rutas absolutas fuera del segmento
- Scripts legacy de ingestion
- "Fallback silencioso"
- Continuar con pack stale

```

**Líneas agregadas**: +25

#### ELIMINAR:
- L100-104: Resources (On-Demand) → Redundante

**Líneas eliminadas**: -5

**Nuevo total**: 113 + 25 - 5 = **133 líneas**

---

### prime.md: De 67 → 85 líneas

#### AGREGAR a [HIGH] Prioridad ALTA:

```markdown
11. `trifecta_dope/src/cli/error_cards.py`
12. `trifecta_dope/tests/acceptance/test_ctx_sync_preconditions.py`
13. `trifecta_dope/src/domain/naming.py`
14. `trifecta_dope/src/infrastructure/daemon_paths.py`
```

**Líneas agregadas**: +4

#### LLENAR [MED] Prioridad MEDIA

```markdown
## [MED] Prioridad MEDIA - Implementación

**Leer para entender bugs recientes y testing.**

1. `trifecta_dope/docs/bugs/create_cwd_bug.md`
2. `trifecta_dope/tests/integration/test_lsp_telemetry.py`
3. `trifecta_dope/src/application/telemetry_reports.py`
4. `trifecta_dope/tests/acceptance/test_cli_smoke_real_use.py`
```

**Líneas agregadas**: +8

#### LLENAR [DICT] Glosario

```markdown
## [DICT] Glosario

| Término | Definición |
|---------|------------|
| **LSP Daemon** | Servidor LSP persistente con UNIX socket IPC, 180s TTL |
| **Error Card** | Sistema de errores estructurados con códigos estables (TRIFECTA_ERROR_CODE) |
| **Context Pack** | Archivo JSON con chunks de documentación indexados |
| **Segment** | Directorio de proyecto con `_ctx/` y configuración Trifecta |
| **Prime File** | `_ctx/prime_{segment_id}.md` - Lista de lectura prioritizada |
| **Dogfooding** | Testing real del CLI usando workflows completos (create→refresh-prime→sync) |
```

**Líneas agregadas**: +8

**Nuevo total**: 67 + 4 + 8 + 8 = **87 líneas**

---

## Separación de Concerns (Roles Clarificados)

### skill.md → "QUÉ y CUÁNDO"

- **Propósito**: Punto de entrada, reglas básicas
- **Audiencia**: Agente nuevo que necesita orientación rápida
- **Contenido**:
  - Onboarding (qué leer primero)
  - Core Rules (4 reglas fundamentales)
  - When to Use (casos de uso)
  - Core Pattern (context cycle básico)
  - Referencias a agent.md para detalles

### agent.md → "CÓMO y CON QUÉ"

- **Propósito**: Manual técnico completo
- **Audiencia**: Agente ejecutando tareas, necesita comandos exactos
- **Contenido**:
  - Tech Stack completo
  - Setup y configuración
  - Protocolos detallados (Session Evidence, STALE)
  - Gates y verificación
  - Troubleshooting

### prime.md → "DÓNDE LEER"

- **Propósito**: Índice prioritizado de archivos
- **Audiencia**: Agente buscando código/docs específicos
- **Contenido**:
  - Paths ordenados por prioridad
  - Glosario de términos
  - Mapa mental (futuro)

---

## Beneficios de la Optimización

### 1. Cumplimiento de Límites

- ✅ skill.md: 75 líneas (25 líneas bajo el límite de 100)
- ✅ Margen para futuras actualizaciones

### 2. Eliminación de Duplicación

- ❌ Resources (On-Demand): Eliminado de agent.md
- ❌ Protocolos detallados: Movidos de skill.md a agent.md
- **Ahorro neto**: 5 líneas de duplicación pura

### 3. Mejor Separación de Concerns

- skill.md: Más conciso, enfocado en "qué hacer"
- agent.md: Más completo, enfocado en "cómo hacerlo"
- prime.md: Más útil, con glosario y paths actualizados

### 4. Mantenibilidad

- Cambios en protocolos → solo agent.md
- Cambios en reglas básicas → solo skill.md
- Nuevos archivos → solo prime.md

---

## Plan de Implementación

### Fase 1: skill.md (Prioridad ALTA)

1. Simplificar CRITICAL PROTOCOL (L29-50)
2. Eliminar STALE FAIL-CLOSED (L52-56)
3. Eliminar Resources (L90-93)
4. Agregar referencia a agent.md en Session Evidence Protocol

**Resultado**: 97 → 75 líneas

### Fase 2: agent.md (Prioridad ALTA)

1. Agregar sección "Protocols" después de Workflow
2. Copiar contenido detallado desde skill.md
3. Eliminar Resources (On-Demand)

**Resultado**: 113 → 133 líneas

### Fase 3: prime.md (Prioridad MEDIA)

1. Agregar 4 paths nuevos a [HIGH]
2. Llenar [MED] con 4 paths
3. Llenar [DICT] con 6 términos

**Resultado**: 67 → 87 líneas

---

## Riesgos y Mitigaciones

### Riesgo 1: agent.md excede límite informal

**Impacto**: 133 líneas puede ser largo para lectura rápida
**Mitigación**: agent.md es "manual técnico", no tiene límite estricto. Es aceptable.

### Riesgo 2: Pérdida de información durante migración

**Impacto**: Comandos críticos podrían perderse
**Mitigación**: Copy-paste exacto de secciones, no reescribir

### Riesgo 3: Referencias rotas

**Impacto**: skill.md referencia agent.md que aún no tiene Protocols
**Mitigación**: Implementar Fase 2 antes de Fase 1, o hacer ambas simultáneamente

---

## Métricas de Éxito

- ✅ skill.md < 100 líneas
- ✅ Cero duplicación de contenido
- ✅ Cada archivo tiene rol claro
- ✅ prime.md tiene secciones llenas (no vacías)
- ✅ Todos los comandos críticos documentados en agent.md

---

## Conclusión

**Recomendación**: IMPLEMENTAR optimización completa.

**Prioridad de ejecución**:

1. **ALTA**: Fase 1 + Fase 2 (skill.md + agent.md) - Elimina duplicación crítica
2. **MEDIA**: Fase 3 (prime.md) - Mejora utilidad pero no urgente

**Esfuerzo estimado**: 15-20 minutos de edición cuidadosa

**Impacto**:

- Mejora significativa en mantenibilidad
- Cumplimiento de límite de 100 líneas en skill.md
- Mejor experiencia para agentes nuevos
