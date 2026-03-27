# Informe: Skill-Hub Discovery Fix

**Fecha:** 2026-03-19
**Estado:** COMPLETADO
**Commit:** `c3dfea7`

---

## Resumen Ejecutivo

Se corrigió un bug estructural en el sistema de discovery de skill-hub donde los archivos administrativos del segmento (skill.md, prime_*.md, agent_*.md, session_*.md) aparecían en los resultados de búsqueda en lugar de solo las skills canónicas.

**Causa raíz:** `BuildContextPackUseCase` asignaba tipo `repo:` a TODOS los archivos .md del segmento sin consultar `skills_manifest.json`.

**Solución:** Política de segmento declarativa + estrategia dedicada + manifest-driven indexing.

---

## Fases Completadas

### Fase 1: SegmentIndexingPolicy (Domain)

**Archivo:** `src/domain/segment_indexing_policy.py`

**Propósito:** Definir política de indexación declarativa para segmentos.

**Implementación:**
```python
class SegmentIndexingPolicy(str, Enum):
    GENERIC = "generic"      # Comportamiento estándar
    SKILL_HUB = "skill_hub"  # Manifest-driven indexing
```

**Método clave:**
- `detect(segment_path)` → Lee `trifecta_config.json` → `indexing_policy`
- Default: `GENERIC` si no hay política explícita

**Tests:** 8 tests
- Default GENERIC cuando no hay config
- Detección de SKILL_HUB cuando está configurado
- Fallback a GENERIC en casos de error

---

### Fase 2: SkillManifest (Domain)

**Archivo:** `src/domain/skill_manifest.py`

**Propósito:** Modelo de dominio para el manifest de skills con validación.

**Estructura:**
```python
@dataclass(frozen=True)
class SkillManifestEntry:
    id: str              # skill:skill-name
    name: str            # skill-name
    relative_path: str   # skill-name.md
    description: str     # Use when...
    source: str          # pi-agent-skills
    canonical: bool      # True
    tags: tuple[str, ...]

@dataclass(frozen=True)
class SkillManifest:
    schema_version: int
    skills: tuple[SkillManifestEntry, ...]
```

**Características:**
- Migración automática v1 → v2
- Validación fail-closed (errores retornan `Err`, no silent skip)
- Chunk ID: `skill:{name}:{content_hash}`

**Tests:** 12 tests
- Carga de manifest válido v2
- Rechazo de entries sin campos requeridos
- Migración v1→v2 con validación de paths
- Rechazo de paths ambiguos en v1

---

### Fase 3: SkillHubIndexingStrategy (Application)

**Archivo:** `src/application/skill_hub_indexing_strategy.py`

**Propósito:** Estrategia de indexación manifest-driven para skill_hub.

**Flujo:**
1. Verifica política es `SKILL_HUB`
2. Carga y valida manifest
3. Construye chunks solo desde entries del manifest
4. Excluye metadata del segmento

**Contrato:**
- Solo entries en manifest son indexadas
- Metadata del segmento excluida (skill.md, prime_*.md, etc.)
- Fail-closed si manifest inválido

**Tests:** 11 tests
- Build exitoso con manifest válido
- Exclusión de metadata del segmento
- Exclusión de archivos no en manifest
- Fallo cuando manifest missing/inválido
- Chunk IDs correctos

---

### Fase 4: BuildContextPackUseCase Integration

**Archivo:** `src/application/use_cases.py`

**Propósito:** Integrar detección de política en el builder existente.

**Cambios:**
```python
def execute(self, target_path: Path) -> Ok[ContextPack] | Err[list[str]]:
    # 0. Detectar política y delegar
    policy = SegmentIndexingPolicy.detect(target_path)

    if policy == SegmentIndexingPolicy.SKILL_HUB:
        strategy = SkillHubIndexingStrategy(target_path)
        result = strategy.build()
        # ... guardar y retornar

    # GENERIC: mantener comportamiento actual (sin cambios)
    ...
```

**Principios:**
- NO hardcodear nombres de segmento
- Backward compatible para GENERIC
- Fail-closed para SKILL_HUB

---

### Fase 5: Tests de Integración

**Archivo:** `tests/unit/test_skill_hub_discovery.py` (actualizado)

**Tests:** 10 tests
- Segment metadata no indexada como skill
- Skills canónicas tienen tipo `skill:`
- Search excluye prime/agent/session metadata
- Integración con segmento real

**Fixture actualizado:**
- `indexing_policy: "skill_hub"` en config
- Manifest v2 con schema correcto

---

### Fase 6: Reindexar Skills-Hub

**Segmento:** `~/.trifecta/segments/skills-hub`

**Cambios aplicados:**

| Archivo | Cambio |
|---------|--------|
| `_ctx/trifecta_config.json` | Agregado `indexing_policy: "skill_hub"` |
| `_ctx/skills_manifest.json` | Regenerado con schema v2 (457 skills) |
| `_ctx/context_pack.json` | Reconstruido con chunks `skill:` type |

**Manifest v2 generado:**
```json
{
  "schema_version": 2,
  "generated_at": "2026-03-19T15:00:00Z",
  "total_skills": 457,
  "skills": [
    {
      "id": "skill:skill-name",
      "name": "skill-name",
      "relative_path": "skill-name.md",
      "source": "skills-hub",
      "description": "...",
      "canonical": true
    }
  ]
}
```

---

### Fase 7: Validar Queries Reales

**Validaciones:**

| Query | Resultado |
|-------|-----------|
| `skill-hub "python"` | 5 hits con tipo `skill:` |
| `skill-hub "manifest indexing"` | indexing-skills-safely como top hit |
| `skill-hub "skill hub overview"` | skills-hub.md como hit |
| Search con términos de metadata | 0 hits de prime/agent/session |

**Verificación técnica:**
```python
# 457 chunks, todos con tipo skill:
skill_chunks = [c for c in pack.chunks if c.id.startswith("skill:")]
assert len(skill_chunks) == 457

# 0 chunks de metadata:
prime_chunks = [c for c in pack.chunks if c.id.startswith("prime:")]
assert len(prime_chunks) == 0
```

---

### Fase 8: Actualizar Skills Afectadas

**Skills actualizadas:**

| Skill | Ubicación | Cambios |
|-------|-----------|---------|
| `skills-hub` | `~/.trifecta/segments/skills-hub/skills-hub.md` | Manifest contract, count 457, exclusions |
| `indexing-skills-safely` | `~/.pi/agent/skills/indexing-skills-safely/SKILL.md` | Manifest v2 contract, updated flow |
| `skill-workflow` | `~/.pi/agent/skills/skill-workflow/SKILL.md` | Manifest contract in Phase 6 |

**Documentación agregada:**
- Formato de manifest v2 con campos requeridos
- Formato de chunk ID: `skill:{name}:{content_hash}`
- Contrato de exclusión de metadata
- Flujo de registro actualizado

---

## Métricas Finales

| Métrica | Valor |
|---------|-------|
| Tests nuevos | 31 |
| Tests totales (suite afectada) | 48 |
| Cobertura de fases | 8/8 (100%) |
| Skills indexadas | 457 |
| Chunks de metadata excluidos | 4 (prime, agent, session, skill) |
| Líneas de código nuevas | ~1,789 |

---

## Archivos Creados/Modificados

```
src/domain/segment_indexing_policy.py         +65 líneas
src/domain/skill_manifest.py                  +282 líneas
src/application/skill_hub_indexing_strategy.py +160 líneas
src/application/use_cases.py                  +29 líneas
tests/unit/test_segment_indexing_policy.py    +155 líneas
tests/unit/test_skill_manifest.py             +357 líneas
tests/unit/test_skill_hub_indexing_strategy.py +318 líneas
tests/unit/test_skill_hub_discovery.py        +426 líneas
```

---

## Contrato Final

| Elemento | Valor |
|----------|-------|
| **SSOT de política** | `trifecta_config.json` → `indexing_policy` |
| **skill_id** | `skill:{name}` - ESTABLE |
| **chunk_id** | `skill:{name}:{content_hash}` - INESTABLE (cambia con contenido) |
| **Metadata excluida** | skill.md, prime_*.md, agent_*.md, session_*.md |
| **Manifest inválido** | FAIL-CLOSED total (no degradación silenciosa) |
| **Backward compat** | Segmentos GENERIC sin cambios |

---

## Lecciones Aprendidas

1. **Política declarativa > Hardcoding:** Usar `indexing_policy` en config permite extensibilidad sin cambios de código

2. **Fail-closed es más seguro:** Errores de manifest causan fallo explícito, no comportamiento indefinido

3. **Chunk ID estable vs inestable:**
   - `skill_id` (estable) para identidad
   - `chunk_id` (inestable) para contenido versionado

4. **Manifest como contrato:** Solo lo que está en manifest es discoverable - sin sorpresas

5. **Tests primero:** Los 31 tests definen el contrato antes de la implementación

---

## Commit

```
c3dfea7 feat(skill-hub): manifest-driven indexing with policy detection

- Add SegmentIndexingPolicy enum for GENERIC vs SKILL_HUB segments
- Add SkillManifest model with v1->v2 migration support
- Add SkillHubIndexingStrategy for manifest-driven indexing
- Integrate policy detection in BuildContextPackUseCase
- Exclude segment metadata (prime, agent, session) from skill_hub index
- Add 31 new tests for skill_hub discovery contract

Fixes: skill-hub returning admin files instead of canonical skills
Contract: Only skills in manifest are discoverable with skill: type
```
