# Auditoría Forense: Provenance y Matriz de Autoridad de skill-hub

**Fecha**: 2026-04-04
**Tipo**: Forense — solo lectura, sin reparación
**Alcance**: Provenance de artefactos críticos, cadena de autoridad, runtime efectivo
**Auditor**: Claude (agente forense)

---

## 1. Veredicto

**El pack vivo fue producido por el builder GENERIC, no por el SKILL_HUB strategy, pese a que la config declara `indexing_policy: "skill_hub"`. La cadena de autoridad del pack está contaminada: el builder autoritativo nunca produjo el artefacto actual. El manifest sí tiene writer canónico identificado (externo al repo), pero su cadena depende de un script fuera de trifecta_dope sin guardrails.**

---

## 2. Provenance del Manifest

### Writer canónico identificado

| Atributo | Valor |
|----------|-------|
| **Archivo** | `~/.pi/agent/skills/indexing-skills-safely/scripts/audit_skill_hub.py` |
| **Función** | `build_manifest()` (líneas 217-235), escritura en líneas 335-338 |
| **Trigger** | Flag `--write-manifest` manual, o `register_skill.py` post-registro |
| **Formato de salida** | Schema v1: `{schema_version:1, generated_at, total_skills, sources, skills[{name, source_path, source, description, tags}]}` |
| **Escribe en disco** | Sí, `Path.write_text()` directo — sin atomic write, sin backup |
| **Externo al repo** | Sí — ubicado en `~/.pi/agent/skills/`, fuera de `trifecta_dope` |

### Writer secundario (trigger)

| Atributo | Valor |
|----------|-------|
| **Archivo** | `~/.pi/agent/skills/indexing-skills-safely/scripts/register_skill.py` |
| **Función** | `rebuild_manifest()` (líneas 290-307), llamada desde `main()` línea 352-355 |
| **Qué hace** | Ejecuta `audit_skill_hub.py --write-manifest --update-docs` como subprocess |
| **Condición** | Post-registro de skill, salvo `--no-manifest-rebuild` |

### Migración en memoria (NO escribe a disco)

| Atributo | Valor |
|----------|-------|
| **Archivo** | `src/domain/skill_manifest.py:209-282` |
| **Función** | `SkillManifest._migrate_v1_to_v2()` |
| **Qué hace** | Migra schema v1→v2 (source_path→relative_path) solo en memoria |
| **Persiste** | No. El archivo en disco permanece en v1 |

### Readers (NO writers)

- `src/infrastructure/aliases_fs.py:204` — `load_skills_manifest()` para generación de aliases
- `src/application/skill_hub_indexing_strategy.py:89` — lee manifest para indexing
- `src/infrastructure/cli.py:1605` — referenciado para keyword extraction

### No encontrados

- Sin backup/restore logic
- Sin freeze/snapshot
- Sin sync desde otra fuente
- Sin CLI command en trifecta que genere manifest
- Sin build/sync hook que lo cree

### Grado de cierre del manifest

**ABIERTO**: Writer canónico identificado pero **externo al repo**, sin guardrails de integridad (no atomic write, no backup, no receipt). El manifest vive y muere por un script en `~/.pi/` que no está versionado en este repo.

---

## 3. Provenance del Pack Vivo

### Estado del pack actual

| Atributo | Valor |
|----------|-------|
| **Archivo** | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` |
| **created_at** | `2026-04-03T14:40:12.066810` (local) |
| **Total IDs** | 336 |
| **doc types** | `skill`, `prime`, `agent`, `session`, `repo:*.md` |
| **ID format** | `skill:2245694c55` (2 segmentos: `{type}:{hash}`) |
| **source_files** | Incluye skill.md, prime, agent, session + ~160 .md de repo scan |

### Estado del backup

| Atributo | Valor |
|----------|-------|
| **Archivo** | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json.bak` |
| **Total IDs** | 914 |
| **ID format** | `skill:README:57fd911904` (3 segmentos: `skill:{filename}:{hash}`) |
| **Producer** | LEGACY (`ingest_trifecta.py`) |

### Comparación de productores vs pack vivo

| Productor | ID format esperado | Match con pack vivo | Incluye metadata | Repo scan |
|-----------|-------------------|---------------------|------------------|-----------|
| **SkillHubIndexingStrategy** | `skill:{name}:{hash}` (3 seg) | NO | NO (excluye) | NO |
| **BuildContextPackUseCase (GENERIC)** | `{type}:{hash}` (2 seg) | **SI** | SI (incluye) | SI |
| **ContextPackBuilder (legacy)** | `skill:{filename}:{hash}` (3 seg) | NO | SI | SI (todo) |

### Evidencia forense del match GENERIC

1. **ID format**: `skill:2245694c55` = `{doc_type}:{content_hash}` — uso de casos.py línea 540: `chunk_id = f"{doc_type}:{content_hash}"`
2. **doc types**: `skill`, `prime`, `agent`, `session`, `repo:*.md` — el GENERIC builder produce exactamente estos doc types
3. **source_files**: Incluye metadata (skill.md, prime, agent, session) — el GENERIC builder los incluye; el SKILL_HUB strategy los excluye (línea 37 del strategy)
4. **repo scan entries**: `repo:gh-address-comments.md`, `repo:angular-architect.md` etc. — el GENERIC builder hace repo scan; el SKILL_HUB NO
5. **chunking_method**: `"whole_file"` — ambos producen esto, no discriminante

### Conclusión del pack

**El pack vivo fue producido por el builder GENERIC.** El SKILL_HUB strategy, que es el builder autoritativo según la config `indexing_policy: "skill_hub"`, NUNCA produjo el pack actual.

El código de delegación existe (`src/application/use_cases.py:313-327`) y fue mergeado el 2026-03-19 (`c3dfea7b`). El pack fue creado el 2026-04-03. La delegación debería haber funcionado. No se pudo determinar por qué el GENERIC builder ejecutó en lugar del SKILL_HUB strategy — queda como **incertidumbre abierta**.

### Timeline de artefactos

```
2026-03-05  Config creado con indexing_policy: "skill_hub"
2026-03-19  Código de delegación SKILL_HUB mergeado (c3dfea7b)
2026-03-19  Pack backup creado (.bak) por LEGACY builder (914 chunks)
2026-04-03 14:40  Manifest generado por audit_skill_hub.py (163 skills)
2026-04-03 14:40  Pack vivo creado por GENERIC builder (336 chunks) ← CONTAMINACIÓN
```

---

## 4. Runtime Efectivo del Usuario

### Wrappers instalados

| Wrapper | Path | Tipo | Verificado |
|---------|------|------|------------|
| `skill-hub` | `~/.local/bin/skill-hub` | Bash (168 líneas) | SI (receipt SHA256) |
| `skill-hub-cards` | `~/.local/bin/skill-hub-cards` | Python (15 líneas) | SI (receipt SHA256) |
| `skill_hub_cards_core.py` | `~/.local/bin/skill_hub_cards_core.py` | Python (606 líneas) | NO en receipt |
| `skill_hub_cards.py` | `~/.local/bin/skill_hub_cards.py` | Python shim (28 líneas) | NO en receipt |

### Camino real hasta query-time

**Cuando el usuario ejecuta `skill-hub "refactor"`:**

```
~/.local/bin/skill-hub (bash)
  → parsea --cards, --limit
  → [sin --cards]:
    → uv run trifecta ctx search --segment "$SEGMENT" --query "$QUERY" --limit 5
    → alias-aware reranking con --explain --explain-format json
    → output: resultados humanos legibles

  → [con --cards / -c]:
    → exec python3 ~/.local/bin/skill-hub-cards
      → importa skill_hub_cards_core.cli()
        → uv run trifecta ctx search --explain --explain-format json
        → uv run trifecta ctx get --mode excerpt
        → output: skill cards (agent-friendly)
```

### Diferencias entre consumidores

| Comando | Qué usa internamente | Output | Estado |
|---------|---------------------|--------|--------|
| `skill-hub "q"` | `trifecta ctx search` (plain + explain) | Humano-legible con reranking | Oficial |
| `skill-hub "q" --cards` | `trifecta ctx search` + `ctx get` | Cards agent-friendly | Oficial |
| `skill-hub-cards "q"` | `trifecta ctx search` + `ctx get` | Cards agent-friendly | Oficial |
| `skill_hub_cards.py "q"` | Delega a `skill-hub-cards` | Igual + deprecation warning | Legacy |
| `trifecta ctx search` | Directo | Raw search output | Debug |
| `trifecta ctx get` | Directo | Raw chunk content | Debug |

### Runtime truth

El usuario **siempre** pasa por `trifecta ctx search` como gateway de queries. No hay bypass. Todas las rutas convergen en el context_pack.json para búsqueda. La diferencia es solo post-procesamiento (reranking, cards, formatting).

---

## 5. Matriz de Autoridad y Contaminación

| Rama | Artefacto que toca | Rol | Estado | Evidencia | Riesgo |
|------|-------------------|-----|--------|-----------|--------|
| **audit_skill_hub.py** (externo) | skills_manifest.json | Producer | **Autoritativo** (de facto) | Único writer. Script externo no versionado | **ALTO**: sin guardrails, sin atomic write, sin receipt |
| **register_skill.py** (externo) | skills_manifest.json | Producer (trigger) | Tolerado | Llama a audit_skill_hub.py post-registro | MEDIO: acoplado al externo |
| **SkillHubIndexingStrategy** | context_pack.json | Producer autoritativo | **NO ejecutado** | Código existe pero pack vivo no tiene su formato de IDs | **CRÍTICO**: builder autoritativo nunca produjo el artefacto vivo |
| **BuildContextPackUseCase (GENERIC)** | context_pack.json | Producer | **Contaminante** | Pack vivo tiene su formato exacto de IDs, incluye metadata, repo scan | **CRÍTICO**: produjo el artefacto pese a policy skill_hub |
| **ContextPackBuilder (legacy)** | context_pack.json | Producer legacy | Legacy inocuo | Solo produjo el .bak, no el pack vivo | BAJO: .bak es histórico |
| **Migración v1→v2 en memoria** | skills_manifest.json | Migrator (in-memory) | Tolerado | No escribe a disco | BAJO: efecto cosmético |
| **skill-hub** (bash wrapper) | Solo lee pack | Consumer/Wrapper | Autoritativo | Delega a trifecta ctx search | BAJO: consumer puro |
| **skill-hub-cards** (python wrapper) | Solo lee pack | Consumer/Wrapper | Autoritativo | Delega a ctx search + ctx get | BAJO: consumer puro |
| **skill_hub_cards_core.py** | Solo lee pack | Consumer/Core logic | Autoritativo | Ejecuta la lógica de cards | BAJO: consumer puro |
| **skill_hub_cards.py** (shim) | Delega todo | Wrapper legacy | Legacy inocuo | Imprime warning, delega via execv | BAJO: transparente |
| **skill-hub-runtime** (promote) | ~/.local/bin/* | Validator/Promotor | Autoritativo | Promueve con SHA256, genera receipt | BAJO: no toca pack/manifest |
| **aliases_fs.py** | Solo lee manifest | Consumer | Tolerado | Lee manifest para keyword extraction | BAJO: consumer puro |
| **Policy detection** | Lee config | Router | Autoritativo | Detecta SKILL_HUB correctamente pero el builder equivocado ejecutó | **ALTO**: la detección funciona pero no se respetó |

---

## 6. Hallazgo Principal

**El builder GENERIC produjo el context_pack.json vivo del segmento skills-hub, no el SkillHubIndexingStrategy. La config declara `indexing_policy: "skill_hub"` y el código de delegación existe, pero el pack tiene la firma forense del builder GENERIC: IDs de 2 segmentos (`skill:hash`), doc types mixtos (`skill`/`prime`/`agent`/`session`/`repo:*`), y source_files que incluyen metadata y repo scan — todo incompatible con el SKILL_HUB strategy que produce IDs de 3 segmentos (`skill:name:hash`) y excluye metadata.**

La cadena de autoridad del pack está **contaminada**: el builder designado como autoridad nunca ejecutó para este artefacto.

---

## 7. Primera Rama a Prohibir

**El builder GENERIC para el segmento skills-hub.** No debería existir ninguna ruta de código que permita al GENERIC builder producir un pack para un segmento con `indexing_policy: "skill_hub"`. Hoy, si la delegación falla silenciosamente o se invoca por un path alternativo, el GENERIC builder toma el control sin advertirlo. Esta rama debe quedar **prohibida**: si el policy es SKILL_HUB y SkillHubIndexingStrategy falla, el build debe fallar (Err), no caer en GENERIC.

---

## 8. Primer Guardrail que Falta

**Fail-closed en la delegación de policy.** Actualmente el código delega al SKILL_HUB strategy y si retorna `Err`, retorna Err. Pero no hay protección contra la ejecución del GENERIC builder cuando el policy es SKILL_HUB. Se necesita un guardrail que:

1. Verifique post-build que el pack producido tiene la firma del builder correcto (formato de IDs, doc types)
2. Impida que el GENERIC builder se ejecute para segmentos con policy SKILL_HUB, incluso si la delegación se invoca por otro path
3. Genere un receipt o checksum del build para permitir verificación forense futura

---

## 9. Incertidumbres Restantes

1. **Por qué el GENERIC builder ejecutó el 2026-04-03**: El código de delegación existía desde 2026-03-19. La config decía skill_hub. No se pudo determinar si fue un bug de dispatch, un path alternativo, o una invocación manual que bypaseó el policy check. Se necesitaría git bisect o log de ejecución para cerrar esta causalidad.

2. **Si el pack fue reconstruido manualmente**: No hay receipt de build para el context_pack (solo para runtime promotion). No hay log de qué comando generó el pack actual. Imposible determinar el comando exacto sin telemetría de build.

3. **Estado del manifest en runtime**: El manifest vive en schema v1 en disco pero se migra a v2 en memoria. No se sabe si algún path de código depende del schema v2 en disco sin migración, lo que podría causar comportamientos divergentes.

4. **Contenido del pack vs manifest**: El pack tiene 336 chunks pero el manifest lista 163 skills. No se verificó si los 163 skills del manifest están todos representados en los 336 chunks del pack, ni si hay chunks huérfanos sin entrada en el manifest.

---

## Archivos Críticos Referenciados

| Archivo | Rol |
|---------|-----|
| `src/application/skill_hub_indexing_strategy.py` | Builder autoritativo SKILL_HUB (nunca ejecutó para el pack vivo) |
| `src/application/use_cases.py:313-327` | Delegación de policy |
| `src/application/use_cases.py:536-540` | GENERIC builder ID generation |
| `src/domain/skill_manifest.py:54-61` | SKILL_HUB chunk_id format |
| `src/domain/segment_indexing_policy.py` | Policy detection |
| `~/.pi/agent/skills/indexing-skills-safely/scripts/audit_skill_hub.py` | Writer canónico del manifest (externo) |
| `~/.trifecta/segments/skills-hub/_ctx/trifecta_config.json` | Config con indexing_policy |
| `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` | Pack vivo (producido por GENERIC) |
| `~/.trifecta/segments/skills-hub/_ctx/context_pack.json.bak` | Pack legacy (producido por LEGACY) |
| `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | Manifest (producido por audit_skill_hub.py) |
| `~/.local/share/trifecta/receipts/skill-hub-runtime.json` | Receipt de runtime promotion |
| `scripts/skill-hub` | Wrapper bash principal |
| `scripts/skill-hub-runtime` | Promotor/verificador de runtime |

---

## Acciones Siguientes (no implementar — solo señalar)

1. Investigar causa raíz del dispatch fallido (git bisect en `use_cases.py`)
2. Implementar fail-closed guardrail en delegación de policy
3. Prohibir GENERIC builder para segmentos SKILL_HUB
4. Reconstruir pack con SkillHubIndexingStrategy y verificar firma
5. Agregar receipt de build con checksum para trazabilidad forense futura
