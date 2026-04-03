# Auditoría integral de `skill-hub` — archivo ancla

Fecha: 2026-04-03
Repo: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope`
Estado: en curso
Owner de esta auditoría: Codex

## Contrato constitucional de esta invocación

- **Modo:** `generate`
- **Target repo root:** `.` (este repo)
- **Canonical source resolution:** `local-verified`
- **Constitution source:** `/Users/felipe_gonzalez/Developer/constitucion-ai/constitution/AGENTIC-CONSTITUTION.md`
- **Jurisdicción:** mejorar este artefacto y dejar más nítida la separación entre:
  - bugs históricos ya mitigados;
  - bugs abiertos en la superficie real;
  - evidencia observada;
  - inferencias operativas;
  - próximos frentes priorizados.

## Leyes aplicadas

- **Ley I — cambio legítimo (Art. 1, 3, 4, 6):** el documento explicita intención, validación usada y coherencia entre hallazgos, evidencia y cierre propuesto.
- **Ley II — lectura previa y no duplicación (Art. 1, 2, 4):** este ancla consolida el estado en un solo artefacto y evita dispersar findings en múltiples resúmenes paralelos.
- **Ley IV — control de versiones, aislamiento y promoción (Art. 2, 4, 7):** el artefacto deja trazabilidad de qué se verificó y qué sigue pendiente sin mezclarlo con superficies externas.
- **Ley VI — fuente de verdad (Art. 1, 2, 3, 4, 6):** este archivo funciona como SSOT local de la auditoría actual; referencias externas sólo entran como evidencia, no como write surface.
- **Ley XII — roles y jurisdicción (Art. 1, 2, 3, 6):** esta mejora se mantiene dentro del rol editor y no intenta mutar la fuente constitucional ni el segmento global fuera de este repo.
- **Ley XIII — primacía conceptual (Art. 1, 3, 5, 6):** la estructura prioriza el razonamiento técnico sobre la acumulación de notas sueltas.

## Objetivo

Construir un inventario único y verificable de:

1. bugs ya identificados previamente en `skill-hub`
2. bugs nuevos descubiertos durante esta auditoría
3. deuda técnica / operativa / de producto / de arquitectura todavía abierta
4. evidencia concreta por superficie para evitar relato sin prueba

## Alcance

Esta auditoría cubre:

- la superficie versionada en este repo;
- la superficie instalada visible para el usuario;
- el segmento vivo `skills-hub` como runtime auditado;
- la coherencia entre arquitectura declarada, corpus persistido, tests y UX observada.

## No objetivos

- No cerrar todavía los bugs.
- No mutar el repo constitucional fuente.
- No mezclar esta auditoría con la campaña de hygiene de PRs.
- No convertir inferencias forenses en “hechos” si no hay evidencia directa.
- No tratar el segmento global externo como write surface desde este artefacto.

## Regla de esta auditoría

- No asumir nada sin evidencia local.
- Separar siempre:
  - bug visible
  - causa raíz
  - drift de superficie/runtime
  - deuda pendiente
- Cada hallazgo debe quedar con:
  - `id`
  - `estado`
  - `tipo`
  - `severidad`
  - `superficie`
  - `evidencia`
  - `impacto`
  - `acción sugerida`

## Convenciones de evidencia

- **Verificado:** comprobado por test, salida de comando o inspección directa del artefacto.
- **Inferido:** conclusión razonable basada en evidencia concreta, pero no validada todavía con una mutación correctiva.
- **Abierto:** problema no resuelto en la superficie real, aunque exista mitigación parcial en repo.
- **Mitigado / verificado:** bug histórico cubierto en código/tests del repo bajo la verificación actual.

## Criterio de cierre de esta auditoría

Esta auditoría sólo podrá considerarse “cerrada” cuando:

1. cada hallazgo relevante tenga evidencia concreta o bloqueo explícito;
2. esté separada la deuda histórica mitigada de la deuda viva de runtime/distribución;
3. exista un orden de ataque priorizado;
4. no queden mezcladas fuente de verdad, observación y propuesta en un mismo bloque ambiguo.

## Superficies bajo auditoría

1. Wrapper instalado: `~/.local/bin/skill-hub`
2. Script versionado: `scripts/skill-hub`
3. Renderer/cards: `scripts/skill-hub-cards`
4. Segmento global: `~/.trifecta/segments/skills-hub`
5. Manifest / contratos: `src/domain/skill_manifest.py`
6. Orquestación sync/reset/search/get:
   - `src/application/reset_context_use_case.py`
   - `src/application/search_get_usecases.py`
   - `src/infrastructure/cli.py`
7. Tests focalizados y aceptación
8. Docs / handoffs / checkpoints relacionados

## Inventario de hallazgos

| ID | Estado | Tipo | Severidad | Superficie | Resumen | Evidencia | Impacto | Acción sugerida |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SH-001 | mitigado / verificado | logic / contract | alta | manifest | `SkillManifest.load()` hoy falla cerrado para schema desconocido, traversal, duplicados e ids inválidos | `src/domain/skill_manifest.py`; `tests/unit/test_skill_manifest.py`; verificación focalizada `39 passed` | El bug histórico principal de contrato quedó cubierto en código y tests | Mantener regression suite y cerrar convergencia persistida `v1→v2` |
| SH-002 | mitigado / verificado | logic / fail-open | alta | sync/reset | El clúster `reset/sync` que reportaba éxito falso quedó corregido en repo | `src/application/reset_context_use_case.py`; `src/application/search_get_usecases.py`; `src/infrastructure/cli.py`; tests focalizados | El bug histórico de éxito falso quedó cubierto en repo | Mantener tests; revisar frentes vecinos como telemetry y wrappers |
| SH-003 | abierto / pendiente de ratificación | operational / governance | alta | wrapper + cadena runtime gobernada | Ya existe una ruta oficial de promoción/verificación con receipt para `skill-hub` y `skill-hub-cards`, y `skill_hub_info_card.py` salió de la cadena directa; el cierre canónico sigue bloqueado porque ADR-004 continúa en `PROPOSED` | `scripts/skill-hub-runtime`; receipt `~/.local/share/trifecta/receipts/skill-hub-runtime.json`; `~/.local/bin/skill-hub` y `~/.local/bin/skill-hub-cards` promovidos | La cadena runtime directa ya no depende del checkout activo para resolver `skill-hub-cards`, pero la gobernanza todavía no está ratificada | Mantener verificación fail-closed y ratificar ADR-004 recién cuando se apruebe la policy |
| SH-004 | abierto | product / architecture / ssot | media | manifest v1→v2 | El manifest persistido sigue en `schema_version: 1` y se migra solo en memoria a v2 | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` muestra `schema_version 1`; `SkillManifest.load()` carga `schema_version 2` en memoria | Hay dos verdades compitiendo: artefacto persistido v1 vs runtime normalizado v2 | Elegir contrato definitivo y convergerlo de forma persistida |
| SH-005 | mitigado / verificado (runtime instalado) | logic / fail-open | alta | wrapper instalado | El wrapper instalado ya preserva el exit status real del search en runtime real, sin seguir colapsándolo a `0` | before: raw `EXIT:2` vs wrapper `EXIT:0`; after: raw `EXIT:2` vs wrapper `EXIT:2`; fix en `~/.local/bin/skill-hub:91-107,215-248` | El runtime instalado dejó de reportar éxito falso ante fallas reales del search | Mantener esta corrección mientras SH-003 siga abierto y converger la superficie instalada a una fuente versionada |
| SH-006 | nuevo / abierto | logic / compatibility | alta | renderer instalado | El renderer instalado parsea solo hits `skill:` pero el corpus vivo entrega principalmente `repo:` | `~/.local/bin/skill_hub_cards.py:46-74`; `context_pack.json` con `repo: 164`; wrapper instalado en `bash` no imprime nada | La UX instalada queda muda aunque haya resultados válidos | Hacer compatible el renderer con IDs reales o converger el corpus |
| SH-007 | nuevo / abierto | product / runtime drift | alta | pack vivo / indexación | El pack vivo del segmento no está convergido con la estrategia manifest-driven: tiene `164` chunks `repo:` y solo `1` `skill:` | `context_pack.json` creado `2026-04-02T09:51:18`; prefijos: `{'skill': 1, 'prime': 1, 'agent': 1, 'session': 1, 'repo': 164}`; `BuildContextPackUseCase` delega a `SkillHubIndexingStrategy` | La superficie real de búsqueda no coincide con el contrato arquitectónico esperado | Re-sincronizar / regenerar el segmento con el flujo correcto y verificar prefijos |
| SH-008 | nuevo / abierto | product / corpus contamination | media | search results / corpus | El corpus vivo sigue mezclando metadata administrativa del hub con skills reales | resultado real `scripts/skill-hub "checkpoint handoff"` incluye `session:97344fc272`; pack incluye `prime`, `agent`, `session`, `skill` metadata | Queries abstractas pueden seguir trayendo metadocs o ruido operacional | Excluir metadocs del espacio principal o degradarlos explícitamente |
| SH-009 | nuevo / abierto | operational / portability debt | media | wrappers / scripts | Tanto el repo script como el wrapper instalado hardcodean `TRIFECTA_ROOT="$HOME/Developer/agent_h/trifecta_dope"` | `scripts/skill-hub:68-82`; `~/.local/bin/skill-hub:32-34,163-166`; `~/.local/bin/skill_hub_cards.py:23-25` | Mover el repo o clonar en otra ruta rompe la herramienta | Resolver root dinámicamente o usar env/config |
| SH-010 | nuevo / abierto | logic / ranking drift | media | repo script reranking | El repo script sigue detectando alias canónicos buscando prefijos `skill:` aunque el corpus vivo devuelve `repo:` | `scripts/skill-hub:136-151`; corpus vivo: `repo:` dominante | El reranking “canonical alias match” puede quedar inoperante o degradado | Alinear el reranking con el ID real o forzar convergencia del corpus |
| SH-011 | nuevo / abierto | operational / robustness | media | telemetry / direct CLI | `ctx search` puede fallar por side-effects de telemetry aun cuando la búsqueda devuelve datos útiles | `src/infrastructure/telemetry.py:95-121,135-190,192-233`; `uv run trifecta ctx search ...` falla por permisos; con `TRIFECTA_NO_TELEMETRY=1` devuelve resultados | En entornos restringidos la búsqueda muere por escritura lateral, no por la búsqueda | Desacoplar éxito funcional de persistencia telemetry o degradar telemetry de forma segura |
| SH-012 | nuevo / abierto | product / output quality | baja | repo cards | El renderer versionado de cards deriva el nombre desde `chunk_id.split(':')[1]`, por eso hoy muestra nombres con sufijo `.md` | `scripts/skill-hub-cards:56-63`; salida real: `# Skill: checkpoint-card.md` | La UX agente-amigable funciona, pero expone nombres no canónicos y más ruidosos | Normalizar nombre visible sin `.md` ni dependencia del prefijo interno |

## Jerarquía de prioridad operativa

### Nota de evidencia — SH-005 (2026-04-03)

- No apareció un generator/packager versionado dentro del repo para el wrapper instalado actual.
- Evidencia directa:
  - `~/.local/bin/skill-hub` **no** es symlink.
  - el contenido instalado **no** coincide con `scripts/skill-hub` ni con un blob versionado equivalente encontrado en la historia revisada.
  - existe evidencia de edición directa in-place del wrapper instalado en sesiones previas (`.pi/agent/sessions/...2026-03-19...jsonl`).
- Clasificación operativa para esta revalidación:
  - la autoridad del **runtime instalado actual** fue tratada como `artifact-authority` (archivo instalado en sí), no como superficie regenerada desde una fuente versionada del repo.
  - por eso SH-005 quedó mitigado en runtime instalado, pero **SH-003 (wrapper drift / distribución)** sigue abierto.

### Prioridad P0 — bloquea verdad operacional visible

- **SH-003** wrapper drift repo vs instalado
- **SH-005** wrapper instalado pierde errores reales
- **SH-006** renderer instalado incompatible con el corpus vivo

**Por qué P0:** son defects user-facing y además distorsionan el diagnóstico porque la herramienta instalada no representa el estado real del repo.

### Prioridad P1 — rompe SSOT / retrieval real

- **SH-007** pack vivo no convergido
- **SH-008** metadata discoverable
- **SH-004** manifest persistido en v1 con normalización runtime a v2
- **SH-010** reranking canónico stale contra IDs reales

**Por qué P1:** aunque arregles el wrapper, el runtime seguiría entregando una verdad mezclada o contaminada.

### Prioridad P2 — degrada robustez y portabilidad

- **SH-011** telemetry acoplada a éxito funcional
- **SH-009** roots hardcodeados
- **SH-012** nombres `.md` en cards del repo

**Por qué P2:** no son el primer cuello de botella conceptual, pero siguen sumando deuda y falsos síntomas.

## Bugs históricos ya listados

### SH-001 — contrato débil de `SkillManifest`
- Estado: mitigado / verificado en repo
- Tipo: `logic / contract`
- Notas:
  - hoy hay tests para schema desconocido, traversal, duplicados e ids sin prefijo `skill:`
  - evidencia principal:
    - `src/domain/skill_manifest.py`
    - `tests/unit/test_skill_manifest.py`
    - verificación focalizada: `39 passed`

### SH-002 — fail-open / éxito falso en `reset` y `sync`
- Estado: mitigado / verificado en repo
- Tipo: `logic / fail-open`
- Notas:
  - ahora `ResetContextUseCase` corta en build `Err`
  - `SyncContextUseCase` deja de devolver éxito falso
  - `ctx sync` falla si stub regeneration falla
  - evidencia principal:
    - `src/application/reset_context_use_case.py`
    - `src/application/search_get_usecases.py`
    - `src/infrastructure/cli.py`
    - `tests/unit/test_reset_and_sync_fail_open.py`
    - `tests/unit/test_cli_sync_stub_regen_fail_closed.py`

### SH-003 — referencia de policy propuesta
- La autoridad conceptual propuesta para SH-003 vive en [ADR-004-skill-hub-runtime-promotion-policy.md](../adr/ADR-004-skill-hub-runtime-promotion-policy.md); este ancla sólo referencia esa policy y no la reemplaza.
- Estado actual verificado: existe una ruta oficial de promoción/verificación en `scripts/skill-hub-runtime`, con receipt persistido en `~/.local/share/trifecta/receipts/skill-hub-runtime.json`.
- Scope gobernado en la implementación actual: `scripts/skill-hub`, `scripts/skill-hub-cards`, `~/.local/bin/skill-hub` y `~/.local/bin/skill-hub-cards`.
- `skill_hub_info_card.py` ya no forma parte de la cadena runtime directa auditada para SH-003.
- La mera existencia del ADR en estado `PROPOSED` no habilita cierre canónico.
- SH-003 sólo podrá cerrarse cuando el ADR esté en `ACCEPTED` y siga existiendo promoción oficial verificable para la instalación vigente y su cadena runtime gobernada.

### SH-004 — convergencia no cerrada del manifest `v1 -> v2`
- Estado: abierto
- Tipo: `product / architecture / ssot`
- Notas:
  - el archivo persistido del segmento global sigue en `schema_version: 1`
  - `SkillManifest.load()` migra y devuelve `loaded_schema_version 2`
  - evidencia:
    - manifest vivo: `schema_version 1`, `skills_count 161`
    - carga runtime vía `uv run python` → `Ok`, `loaded_schema_version 2`

## Nuevos hallazgos de esta corrida

### SH-005 — wrapper instalado pierde errores reales
- Estado: abierto
- Tipo: `logic / fail-open`
- Severidad: alta
- Evidencia:
  - `~/.local/bin/skill-hub:91-97`
  - `output="$(...)" || true` seguido por `status=$?`
- Lectura:
  - esa construcción pisa el exit status real con el del `true`
  - o sea: el wrapper puede seguir como si nada aunque el search haya fallado

### SH-006 — renderer instalado roto contra el corpus vivo
- Estado: abierto
- Tipo: `logic / compatibility`
- Severidad: alta
- Evidencia:
  - `~/.local/bin/skill_hub_cards.py:46-74` parsea solo `\[skill:...`
  - prueba aislada: alimentado con output real `repo:` devuelve `# No skills found`
  - el pack vivo contiene `repo: 164` chunks y solo `skill: 1`
- Lectura:
  - el renderer instalado quedó acoplado a un formato de ids que hoy NO representa al corpus vivo

### SH-007 — el pack vivo no refleja el contrato manifest-driven esperado
- Estado: abierto
- Tipo: `product / runtime drift`
- Severidad: alta
- Evidencia:
  - `BuildContextPackUseCase` delega a `SkillHubIndexingStrategy` cuando `indexing_policy == skill_hub`
  - `trifecta_config.json` vivo tiene `"indexing_policy": "skill_hub"`
  - aun así, `context_pack.json` creado el `2026-04-02T09:51:18.662225` tiene:
    - `skill: 1`
    - `prime: 1`
    - `agent: 1`
    - `session: 1`
    - `repo: 164`
- Lectura:
  - la arquitectura dice una cosa, la superficie persistida dice otra
  - eso es drift de runtime / convergencia operativa no cerrada

### SH-008 — contaminación de corpus por metadata del hub
- Estado: abierto
- Tipo: `product / retrieval quality`
- Severidad: media
- Evidencia:
  - `scripts/skill-hub "checkpoint handoff"` devolvió:
    - `repo:checkpoint-card.md:...`
    - `repo:code-review-agent.md:...`
    - `session:97344fc272`
  - el pack vivo incluye entradas `prime`, `agent`, `session` y `skill` metadata
  - `docs/reports/skill_hub_phase6_recovery_postmortem.md` ya documentaba este patrón
  - verificación actual:
    - `uv run pytest -q tests/unit/test_skill_hub_discovery.py tests/unit/test_skill_hub_indexing_strategy.py tests/unit/test_skill_manifest.py tests/unit/test_segment_indexing_policy.py`
    - resultado: `1 failed, 47 passed`
    - failure real:
      - `TestRealSkillsHubSegment.test_real_segment_metadata_not_discoverable`
      - encontró `prime:efbc132df7`
- Lectura:
  - el hub sigue compitiendo contra sus propios metadocs en queries abstractas

### SH-009 — roots hardcodeados
- Estado: abierto
- Tipo: `operational / portability debt`
- Severidad: media
- Evidencia:
  - `scripts/skill-hub:68-82`
  - `~/.local/bin/skill-hub:32-34,163-166`
  - `~/.local/bin/skill_hub_cards.py:23-25`
- Lectura:
  - mover el repo o usar otra máquina/ruta rompe el surface

### SH-010 — canonical alias reranking stale en repo script
- Estado: abierto
- Tipo: `logic / ranking drift`
- Severidad: media
- Evidencia:
  - `scripts/skill-hub:136-151` busca `skill:{term}:`
  - el corpus vivo devuelve mayormente `repo:{name}.md:{hash}`
- Lectura:
  - aunque el repo script sí devuelva resultados, esa rama de reranking quedó desalineada con el ID real del pack

### SH-011 — telemetry puede romper un search funcional
- Estado: abierto
- Tipo: `operational / robustness`
- Severidad: media
- Evidencia:
  - sin `TRIFECTA_NO_TELEMETRY=1`, `uv run trifecta ctx search --segment ~/.trifecta/segments/skills-hub --query checkpoint --limit 3` falla por `PermissionError` al escribir:
    - `events.jsonl`
    - `last_run.json`
  - con `TRIFECTA_NO_TELEMETRY=1`, el mismo search devuelve resultados
  - código relevante:
    - `src/infrastructure/telemetry.py:95-121`
    - `src/infrastructure/telemetry.py:135-190`
    - `src/infrastructure/telemetry.py:192-233`
- Lectura:
  - telemetry no es puramente observabilidad; hoy puede convertirse en condición fatal de la ejecución

### SH-012 — cards del repo exponen nombres no canónicos
- Estado: abierto
- Tipo: `product / output quality`
- Severidad: baja
- Evidencia:
  - `scripts/skill-hub-cards:56-63` toma `parts[1]` del `chunk_id`
  - salida real observada: `# Skill: checkpoint-card.md`
- Lectura:
  - no rompe el flujo, pero sí ensucia el surface agente-amigable con nombres `.md`

## Evidencia bruta

### Comandos ejecutados

- `scripts/skill-hub "audit a CLI tool for logic bugs operational debt product issues and architecture"`
- `scripts/skill-hub "systematically audit a CLI for latent bugs fail-open paths wrapper drift and contract mismatches"`
- `scripts/skill-hub "write a markdown audit anchor document with findings evidence severity and next actions"`
- `bash scripts/skill-hub "checkpoint handoff"`
- `bash scripts/skill-hub --cards checkpoint handoff`
- `/Users/felipe_gonzalez/.local/bin/skill-hub --plain checkpoint handoff` (runner en `bash`)
- `uv run pytest -q tests/unit/test_skill_manifest.py tests/unit/test_reset_and_sync_fail_open.py tests/unit/test_cli_sync_stub_regen_fail_closed.py tests/unit/test_cli_build_sync_parity.py tests/acceptance/test_ctx_sync_preconditions.py`
- `uv run pytest -q tests/unit/test_skill_hub_discovery.py tests/unit/test_skill_hub_indexing_strategy.py tests/unit/test_skill_manifest.py tests/unit/test_segment_indexing_policy.py`
- inspección de:
  - `src/domain/skill_manifest.py`
  - `src/application/reset_context_use_case.py`
  - `src/application/search_get_usecases.py`
  - `src/application/use_cases.py`
  - `src/application/skill_hub_indexing_strategy.py`
  - `src/infrastructure/cli.py`
  - `src/infrastructure/telemetry.py`
  - `scripts/skill-hub`
  - `scripts/skill-hub-cards`
  - `~/.local/bin/skill-hub`
  - `~/.local/bin/skill_hub_cards.py`
- inspección del segmento vivo:
  - `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`
  - `~/.trifecta/segments/skills-hub/_ctx/trifecta_config.json`
  - `~/.trifecta/segments/skills-hub/_ctx/context_pack.json`
- búsqueda directa:
  - `TRIFECTA_NO_TELEMETRY=1 uv run trifecta ctx search --segment ~/.trifecta/segments/skills-hub --query checkpoint --limit 3`

### Archivos inspeccionados

- `docs/reports/2026-03-19-skill-hub-discovery-fix-audit-report.md`
- `docs/reports/skill_hub_phase6_recovery_postmortem.md`
- `_ctx/plans/2026-04-01-origin-pr-hygiene/anchor.md`
- `docs/auditoria/PR_SEQUENCE_SKILLHUB_AUDIT.md`
- todos los archivos listados en “Comandos ejecutados”

## Resumen operativo provisorio

- **Lo corregido en repo está corregido**:
  - contratos de `SkillManifest`
  - fail-open de `reset/sync`
  - verificación focalizada actual: `39 passed`
- **Lo no cerrado en superficie real sigue vivo**:
  - drift del wrapper instalado
  - renderer instalado incompatible con el corpus vivo
  - manifest persistido todavía en v1
  - pack vivo no convergido al contrato manifest-driven esperado
  - contaminación del corpus por metadata del propio hub
  - roots hardcodeados
  - telemetry demasiado acoplada a éxito de ejecución
- **La prueba más fuerte de que sigue vivo**:
  - la suite histórica de discovery/indexing no quedó totalmente verde contra el segmento real
  - hoy falla exactamente el caso de metadata discoverable (`prime:*`)

## Decisión operativa recomendada

### Secuencia recomendada

1. **P0 de distribución/runtime visible**
   - SH-005
   - SH-006
   - SH-003
2. **P1 de SSOT/corpus real**
   - SH-007
   - SH-008
   - SH-004
   - SH-010
3. **P2 de robustez/portabilidad**
   - SH-011
   - SH-009
   - SH-012

### Justificación

Primero hay que hacer que la superficie que usa la persona no mienta.  
Después hay que hacer que el corpus/runtime real coincida con el contrato arquitectónico.  
Recién ahí conviene pulir robustez y ergonomía.

## Próximos pasos dentro de esta misma auditoría

1. Convertir este ancla en SSOT explícita del frente `skill-hub` mientras dure esta ronda.
2. Si se abre ejecución, arrancar por P0 para alinear repo surface vs installed surface.
3. Después atacar P1 para reconciliar runtime/corpus con la arquitectura manifest-driven.
4. Cerrar con una nueva verificación que distinga:
   - tests de repo,
   - tests contra segmento real,
   - smoke del wrapper instalado,
   - smoke del repo script.
