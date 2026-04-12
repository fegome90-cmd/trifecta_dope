# INFORME: Diagnóstico skill-hub Discovery Bug

**Estado:** EN PROGRESO
**Fecha:** 2026-03-19
**Autor:** Trifecta Team

---

## 1. CAUSA RAÍZ REAL

**Capa afectada: INDEXACIÓN (BuildContextPackUseCase)**

El problema está en `src/application/use_cases.py`, método `execute()` de `BuildContextPackUseCase`.

### Evidencia

1. **Pipeline de build no consulta `skills_manifest.json`**:
   - El builder asigna tipo `repo:<filename>:hash` a TODOS los archivos `.md` del segmento
   - No existe lógica para distinguir skills canónicas de metadatos
   - `skills_manifest.json` se usa solo para extracción de aliases, NO para tipar chunks

2. **Metadatos del segmento se indexan como entidades discoverable**:
   - `skill.md` del segmento → tipo `skill:hash` (debería ser NO-discoverable)
   - `prime_skills-hub.md` → tipo `prime:hash` (aparece en resultados)
   - `agent_skills-hub.md` → tipo `agent:hash` (aparece en resultados)
   - `session_skills-hub.md` → tipo `session:hash` (aparece en resultados)

3. **Evidencia del context_pack.json real**:
```
skill:3a37012894: skill.md              ← Segmento metadata, NO skill canónica
prime:efbc132df7: prime_skills-hub.md   ← Metadata administrativo
agent:5565645148: agent_skills-hub.md   ← Metadata administrativo
session:97344fc272: session_skills-hub.md ← Metadata administrativo
repo:code-review-agent.md:70c84f920b    ← Skill canónica pero con tipo WRONG
```

4. **Test de integración confirma el bug**:
```
AssertionError: Found prime metadata: prime:efbc132df7
```

---

## 2. CAPA CORREGIDA

**INDEXACIÓN** - `BuildContextPackUseCase.execute()`

**Por qué NO es retrieval ni render:**
- Retrieval (`ContextService.search()`) no tiene información para distinguir tipos
- El tipo se asigna en build y persiste en `context_pack.json`
- Render solo muestra lo que el índice contiene

**Cambio requerido:**
- Consultar `skills_manifest.json` durante build
- Asignar tipo `skill:` a archivos que están en el manifest
- Asignar tipo `metadata:` (o excluir del índice) a archivos del propio segmento

---

## 3. CONTRATO NUEVO/RESTAURADO

### 3.1 Definición de "Discoverable Skill"

Un chunk es discoverable como skill si y solo si:

```
1. Existe en skills_manifest.json con:
   - id: string (required, estable, hash o slug único)
   - name: string (required, no vacío)
   - relative_path: string (required, path relativo al segmento)
   - description: string (required)
   - source: string (required)
   - canonical: boolean (opcional, default True)

2. Su tipo en context_pack.json es "skill:" (no "repo:", "prime:", etc.)

3. NO es metadata del segmento (skill.md, prime_*.md, agent_*.md, session_*.md del segmento host)
```

### 3.2 Estructura de skills_manifest.json (Schema v2)

```json
{
  "schema_version": 2,
  "skills": [
    {
      "id": "skill:code-review-agent",
      "name": "code-review-agent",
      "relative_path": "code-review-agent.md",
      "source": "pi-agent-skills",
      "description": "Use for code review workflows...",
      "canonical": true,
      "tags": ["review", "code-quality"]
    }
  ]
}
```

**NOTA:** La política del segmento (`indexing_policy`) se declara en `trifecta_config.json`, NO aquí.

### 3.3 Rol de aliases.yaml

```
aliases.yaml = MAPA de alias → skill names (NO gate de validez)
skills_manifest.json = SSOT de existencia de skills
```

- Un alias puede apuntar a una skill que no existe (search devuelve vacío, no error)
- Una skill existe si está en manifest, independientemente de aliases

### 3.4 Política de Segmento (SSOT Único)

| Política | Comportamiento |
|----------|----------------|
| `generic` (default) | Comportamiento actual, sin manifest-driven typing |
| `skill_hub` | Manifest-driven, solo entries en manifest son discoverable |

**SSOT:** La política se declara **ÚNICAMENTE** en `trifecta_config.json` → campo `indexing_policy`.

```json
// _ctx/trifecta_config.json
{
  "segment_id": "skills-hub",
  "repo_root": "/path/to/segment",
  "indexing_policy": "skill_hub"  // ← SSOT de política
}
```

**No hay doble autoridad:** `skills_manifest.json` NO tiene campo `segment_policy`.

### 3.5 Identidad: skill_id vs chunk_id

**Dos conceptos distintos:**

| Concepto | Definición | Estabilidad | Uso |
|----------|------------|-------------|-----|
| `skill_id` | Identidad de dominio de la skill | **ESTABLE** - No cambia entre builds | Referencias en aliases, manifest, logs |
| `chunk_id` | Identidad del chunk en context_pack | **INESTABLE** - Puede cambiar si esquema cambia | Búsqueda interna, indexación |

**Formato:**
```
skill_id:  "skill:{name}"                    ej: "skill:code-review-agent"
chunk_id:  "skill:{skill_id}:{content_hash}" ej: "skill:skill:code-review-agent:a1b2c3d4"
```

**Contrato:**
- `skill_id` se deriva del campo `id` del manifest (o `name` si no hay `id`)
- `chunk_id` = `{type}:{skill_id}:{hash}` donde hash es de contenido
- Si el esquema cambia, `chunk_id` puede cambiar pero `skill_id` permanece igual
- Aliases resuelven a `skill_id`, no a `chunk_id`

### 3.6 Destino de Metadata del Segmento

**Decisión: EXCLUIR DEL ÍNDICE**

| Archivo | Comportamiento |
|---------|----------------|
| `skill.md` | NO indexado |
| `_ctx/prime_*.md` | NO indexado |
| `_ctx/agent_*.md` | NO indexado |
| `_ctx/session_*.md` | NO indexado |

**Razón:** Estos archivos son metadata del segmento host, no skills discoverable. Indexarlos (incluso como no-discoverable) contamina el índice con contenido irrelevante para búsqueda.

**Costo operativo:** Si se necesita buscar metadata del segmento, usar `trifecta ctx get` directo con IDs conocidos, no search.

### 3.7 Política para Manifest Inválido

**Decisión: FAIL-CLOSED TOTAL**

En modo `skill_hub`, si el manifest es inválido:
- **NO** se permite build con degradación silenciosa
- **NO** se permite "silently skipped" de entradas inválidas
- Se devuelve error explícito con diagnóstico

**Casos de fallo:**
| Condición | Resultado |
|-----------|-----------|
| `skills_manifest.json` no existe | `Err(["Manifest not found: skill_hub requires skills_manifest.json"])` |
| JSON inválido (parse error) | `Err(["Manifest parse error: {details}"])` |
| Falta campo requerido en entry | `Err(["Invalid manifest entry at index {i}: missing required field '{field}'"])` |
| `relative_path` no existe en disco | `Err(["Manifest entry '{name}' references missing file: {relative_path}"])` |

**Justificación:** Un skill hub con manifest corrupto es un estado de error del sistema, no degradable. Degradación silenciosa enmascara problemas y genera comportamiento impredecible.

### 3.8 Migración v1→v2

**Estrategia: MIGRACIÓN VERIFICABLE CON RECHAZO DE AMBIGUOS**

```python
def migrate_manifest_v1_to_v2(v1: dict, segment_path: Path) -> Ok[dict] | Err[list[str]]:
    """
    Migra manifest schema_version 1 a 2.
    
    RECHAZA casos ambiguos:
    - source_path que no termina en SKILL.md
    - nombre que no se puede derivar del path
    - archivo referenciado no existe en disco
    """
    errors = []
    skills_v2 = []
    
    for i, skill in enumerate(v1.get("skills", [])):
        # 1. Validar source_path existe
        source_path = skill.get("source_path", "")
        if not source_path:
            errors.append(f"Entry {i}: missing source_path")
            continue
            
        # 2. Validar patrón esperado (termina en SKILL.md)
        if not source_path.endswith("/SKILL.md"):
            errors.append(f"Entry {i}: source_path must end with /SKILL.md, got: {source_path}")
            continue
            
        # 3. Derivar relative_path (sin heurísticas frágiles)
        # source_path: /abs/path/to/skill-name/SKILL.md
        # relative_path: skill-name.md (nombre del directorio padre + .md)
        skill_dir = Path(source_path).parent.name
        if not skill_dir:
            errors.append(f"Entry {i}: cannot derive skill name from source_path")
            continue
            
        relative_path = f"{skill_dir}.md"
        
        # 4. Validar que el archivo existe en el segmento
        expected_file = segment_path / relative_path
        if not expected_file.exists():
            errors.append(f"Entry {i}: derived file not found: {relative_path}")
            continue
            
        # 5. Generar skill_id estable
        skill_id = f"skill:{skill_dir}"
        
        # 6. Construir entry v2
        skills_v2.append({
            "id": skill_id,
            "name": skill.get("name", skill_dir),
            "relative_path": relative_path,
            "description": skill.get("description", ""),
            "source": skill.get("source", "unknown"),
            "canonical": skill.get("canonical", True),
        })
    
    if errors:
        return Err(errors)
    
    return Ok({
        "schema_version": 2,
        "skills": skills_v2,
    })
```

**Contrato de migración:**
- Si hay AMBIGÜEDAD → rechazar con error específico
- No adivinar, no asumir defaults para campos críticos
- Log detallado de cada transformación para auditoría

### 3.9 Tipos de Chunk en context_pack.json

| Tipo | Uso | Discoverable | Formato ID |
|------|-----|--------------|------------|
| `skill:` | Skills canónicas del manifest | **SÍ** | `skill:{skill_id}:{hash}` |
| `repo:` | Archivos del repo no en manifest | NO | `repo:{path}:{hash}` |

---

## 4. TESTS AGREGADOS

Archivo: `tests/unit/test_skill_hub_discovery.py`

### 4.1 Tests de Contrato

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_segment_metadata_not_indexed_as_skill` | skill.md del segmento NO debe ser tipo skill: | RED |
| `test_canonical_skill_has_skill_type` | Skills en manifest deben ser tipo skill: | RED |
| `test_search_excludes_segment_metadata` | prime/agent/session NO en resultados | RED |
| `test_manifest_has_required_fields` | Validar campos obligatorios | GREEN |
| `test_manifest_invalid_entry_excluded` | Entradas sin name se excluyen | GREEN |
| `test_alias_resolves_to_canonical_skill` | Alias funciona como mapa | GREEN |
| `test_alias_not_gate_of_validity` | aliases.yaml no es gate | GREEN |
| `test_renderer_rejects_non_skill_entities` | Contrato de tipos válidos | GREEN |
| `test_real_segment_metadata_not_discoverable` | Integración segmento real | RED |

### 4.2 Tests de Política (SSOT)

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_policy_ssot_from_config_only` | Política solo de trifecta_config.json | PENDING |
| `test_policy_no_conflict_possible` | Demostrar que no puede haber conflicto (única fuente) | PENDING |
| `test_generic_segment_without_manifest` | Segmento genérico sin manifest mantiene comportamiento | PENDING |
| `test_skill_hub_without_manifest_fails_closed` | Skill hub sin manifest falla cerrado | PENDING |
| `test_skill_hub_invalid_manifest_fails_closed` | Skill hub con manifest corrupto falla cerrado | PENDING |

### 4.3 Tests de Identidad

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_skill_id_is_stable` | skill_id no cambia entre builds | PENDING |
| `test_chunk_id_includes_skill_id` | chunk_id contiene skill_id | PENDING |
| `test_chunk_id_changes_on_content_change` | chunk_id cambia si contenido cambia | PENDING |
| `test_alias_resolves_to_skill_id_not_chunk_id` | Alias resuelve a skill_id | PENDING |

### 4.4 Tests de Metadata

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_segment_metadata_excluded_from_index` | skill.md, prime_, agent_, session_ no indexados | PENDING |
| `test_segment_metadata_not_searchable` | Búsqueda de "metadata segment" no retorna archivos host | PENDING |

### 4.5 Tests de Migración

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_migration_v1_to_v2_success` | Migración válida funciona | PENDING |
| `test_migration_v1_rejects_ambiguous_path` | Path sin SKILL.md rechazado | PENDING |
| `test_migration_v1_rejects_missing_file` | Archivo referenciado no existe rechazado | PENDING |
| `test_migration_v1_rejects_missing_source_path` | Entry sin source_path rechazado | PENDING |

### 4.6 Tests de Compatibilidad

| Test | Propósito | Estado |
|------|-----------|--------|
| `test_id_stability_on_reclassification` | skill_id estable al cambiar de repo: a skill: | PENDING |
| `test_generic_segment_unaffected` | Segmentos generic sin cambios | PENDING |

---

## 5. EVIDENCIA ANTES/DESPUÉS

### ANTES (actual)

```bash
$ skill-hub "como crear una skill"

1. [skill:3a37012894] skill.md              ← WRONG: metadata
2. [prime:efbc132df7] prime_skills-hub.md   ← WRONG: metadata
3. [agent:5565645148] agent_skills-hub.md   ← WRONG: metadata
4. [session:97344fc272] session_skills-hub.md ← WRONG: metadata
```

```bash
$ skill-hub "refactor"

1. [repo:code-review-agent.md:70c84f920b]   ← WRONG: debería ser skill:
```

### DESPUÉS (esperado)

```bash
$ skill-hub "como crear una skill"

1. [skill:abc123] skill-creator.md          ← Solo skills canónicas
2. [skill:def456] skill-creation-guide.md   ← Sin metadatos
```

```bash
$ skill-hub "refactor"

1. [skill:xyz789] code-review-agent.md      ← Tipo correcto
2. [skill:ghi012] refactoring-expert.md     ← Solo skills
```

---

## 6. RIESGOS RESIDUALES

### Riesgo 1: skills_manifest.json desactualizado
- **Impacto:** Skills nuevas no aparecen hasta reindexar manifest
- **Mitigación:** Documentar que sync del manifest es requisito

### Riesgo 2: Skills con nombres duplicados en distintas fuentes
- **Impacto:** Colisión de nombres, comportamiento indefinido
- **Mitigación:** Namespacing por source en el nombre (ej: `anthropic:canvas-design`)

### Riesgo 3: Segmentos sin skills_manifest.json
- **Impacto:** No se descubren skills, solo contenido repo
- **Mitigación:** Fallback a comportamiento actual para segmentos sin manifest

### Riesgo 4: Breakage de consumers que esperan tipos actuales
- **Impacto:** Código que filtra por `repo:` type se rompe
- **Mitigación:** Comunicar cambio de contrato, versión de schema

### Riesgo 5: Archivos orphan (en repo pero no en manifest)
- **Impacto:** Contenido legítimo no discoverable
- **Mitigación:** Validación en build, warnings para orphans

### Riesgo 6: Estabilidad de IDs al cambiar clasificación
- **Impacto:** IDs cambian de `repo:file:hash` a `skill:hash`, invalida caches
- **Mitigación:** Usar ID estable del manifest, no derivado de tipo

---

## 7. DISEÑO DE POLÍTICA DE SEGMENTO (SSOT ÚNICO)

### 7.1 Ubicación de la Política

**SSOT:** `trifecta_config.json` → campo `indexing_policy`

**No hay doble autoridad.** El manifest NO tiene campo de política.

```python
# src/domain/segment_indexing_policy.py

class SegmentIndexingPolicy:
    """Política de indexación para un segmento."""
    
    GENERIC = "generic"        # Comportamiento actual
    SKILL_HUB = "skill_hub"    # Manifest-driven, fail-closed
    
    @classmethod
    def detect(cls, segment_path: Path) -> str:
        """
        Detecta la política del segmento.
        
        SSOT: trifecta_config.json → indexing_policy field
        Default: GENERIC
        """
        config_path = segment_path / "_ctx" / "trifecta_config.json"
        
        if not config_path.exists():
            return cls.GENERIC
            
        try:
            data = json.loads(config_path.read_text())
            policy = data.get("indexing_policy", cls.GENERIC)
            
            if policy == cls.SKILL_HUB:
                return cls.SKILL_HUB
            return cls.GENERIC
            
        except (json.JSONDecodeError, KeyError):
            return cls.GENERIC
```

### 7.2 Por qué NO hay conflicto posible

1. **Única fuente:** Solo `trifecta_config.json` define la política
2. **No hay campo en manifest:** `skills_manifest.json` no tiene `segment_policy`
3. **Default explícito:** Si no hay config o no hay campo, es `GENERIC`

### 7.3 Cómo evita contaminar el builder genérico

```
BuildContextPackUseCase.execute():
    │
    ├─→ policy = SegmentIndexingPolicy.detect(segment_path)
    │
    ├─→ if policy == GENERIC:
    │       └─→ _build_generic(segment)  # ← SIN CAMBIOS
    │
    └─→ if policy == SKILL_HUB:
            └─→ SkillHubIndexingStrategy.build(segment)
                    │
                    ├─→ Cargar manifest (required)
                    ├─→ Validar schema_version == 2
                    ├─→ Validar campos requeridos en cada entry
                    ├─→ Validar archivos existen en disco
                    ├─→ Si cualquier validación falla → Err([...])
                    ├─→ Clasificar: manifest entry → skill:, otros → excluidos
                    └─→ Retornar ContextPack
```

**El builder genérico NO se contamina porque:**
- `_build_generic()` permanece intacto (mismo código que hoy)
- Lógica específica en `SkillHubIndexingStrategy` (archivo separado)
- Detección de política es declarativa, no hardcoded names

---

## 8. ACTUALIZACIÓN DE SKILLS AFECTADAS (PASO FINAL)

Después del fix, las skills que creamos para usar y configurar skill-hub quedarán desactualizadas. Requieren actualización:

### 8.1 Skills a Actualizar

| Skill | Ubicación | Cambio Requerido |
|-------|-----------|------------------|
| `skill-workflow` | `~/.pi/agent/skills/skill-workflow/` | Actualizar docs para reflejar nuevo contrato |
| `skill-creator` | `~/.agents/skills/anthropic-skills/skills/skill-creator/` | Ajustar generación para incluir campos obligatorios |
| Cualquier skill que documente skill-hub | Varios | Referencias al contrato nuevo |

### 8.2 Checklist de Actualización

```markdown
[ ] skill-workflow/SKILL.md
    - Actualizar sección "Cómo funciona skill-hub"
    - Documentar campos obligatorios de manifest
    - Aclarar rol de aliases.yaml

[ ] skill-creator/SKILL.md (si aplica)
    - Incluir campos obligatorios en template generado
    - Agregar validación de manifest

[ ] AGENTS.md (pi-agent)
    - Actualizar referencia a skill-hub si existe

[ ] Documentación de skills_manifest.json
    - Crear/editar docs/reports/skill_manifest_contract.md
```

### 8.3 Orden de Ejecución Completo

```
1. Crear dominio de política de segmento
2. Crear estrategia de indexación SkillHubIndexingStrategy
3. Modificar BuildContextPackUseCase para usar política
4. Tests pasan
5. Reindexar skills-hub
6. Validar queries
7. Actualizar skill-workflow y skills afectadas ← PASO FINAL
8. Comunicar cambio de contrato a usuarios
```

---

## 9. PROGRESO

- [x] Diagnóstico de causa raíz
- [x] Tests de regresión escritos (RED)
- [x] Diseño de política de segmento
- [ ] Implementación de SegmentPolicy
- [ ] Implementación de SkillHubIndexingStrategy
- [ ] Modificación de BuildContextPackUseCase
- [ ] Tests pasan (GREEN)
- [ ] Reindexar skills-hub
- [ ] Validar queries reales
- [ ] Actualizar skills afectadas
