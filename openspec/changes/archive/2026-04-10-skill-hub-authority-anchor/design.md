# Design: Skill-hub Authority Anchor

## Technical Approach

Reorder `skill_hub` around one governed chain:

`staging input -> canonical manifest -> promotion transaction -> promoted artifact set -> runtime consumption`

Authority lives only in:
1. canonical normalized manifest
2. promoted `skill_hub` pack
3. promotion receipt for the promoted set

Everything else is staging, evidence, or derived output.

## Final Authority Matrix

| Surface | Owner único | Writer autorizado | Readers autorizados | ¿Autoritativa? | Contracto | Fallback | Fail-closed | Evidence/receipt |
|---|---|---|---|---|---|---|---|---|
| Upstream manifest input | external inventory toolchain | `audit_skill_hub.py --write-manifest` | admission only | No | staging inventory only | Prohibido | invalid input blocks admission | staging fingerprint |
| Canonical normalized manifest | Trifecta admission boundary | governed normalization/persist step | `SkillHubIndexingStrategy`, aliases/CLI, validators | Sí | one schema, `relative_path`, explicit `canonical` | Prohibido | invalid manifest blocks promotion | manifest receipt |
| Skill_hub context pack | Trifecta governed build | `BuildContextPackUseCase` + `SkillHubIndexingStrategy` only | `ContextService`, `ctx search`, `ctx get` | Sí | `skill:*` corpus only, no metadata families | Prohibido | invalid pack blocks promotion | pack receipt |
| Promotion transaction / promoted artifact set | Trifecta promotion gate | single atomic promotion path | runtime gate, humans, CI | Sí | promoted set is all-or-nothing | Prohibido | partial promotion is invisible | promotion receipt |
| Admission / validation receipt | Trifecta promotion gate | receipt writer inside promotion path | humans, CI, runtime guard | No | evidence only, immutable | Prohibido | no receipt => not promoted | receipt itself |
| Runtime load surface | `ContextService` | none | runtime callers only | No | reads promoted pack only | Prohibido | missing/unsealed pack => runtime error | valid promoted-set receipt |
| Aliases / CLI consumption surface | Trifecta alias consumer boundary | none for manifest; alias derivation only | `aliases_fs.py`, `cli_skills.py`, CLI expansion | No | canonical manifest is only semantic source | Prohibido | invalid canonical manifest => explicit failure | manifest receipt + alias generation report |

## Promotion Contract

### Required inputs
- declared segment policy `indexing_policy=skill_hub`
- canonical normalized manifest candidate
- skill files referenced by the manifest
- prior promoted set pointer, if one exists

### Pre-validations
- manifest schema is canonical
- every canonical entry resolves to an existing file
- builder path is the governed `skill_hub` path, never generic
- runtime target paths are writable atomically

### Closure checks
- promoted pack discoverable set equals canonical manifest `canonical=true` set
- every pack chunk id is `skill:*`
- no `repo:`, `prime:`, `agent:`, `session:` families
- receipt fingerprints match manifest + pack pair

### Artifacts written
- canonical `_ctx/skills_manifest.json`
- canonical `_ctx/context_pack.json`
- promotion/admission receipt for the promoted set
- optional derived alias artifacts after the promoted set exists

### Atomicity conditions
- manifest, pack, and receipt become visible as one promoted set
- no reader may observe a new manifest with an old pack, or vice versa
- alias derivation is downstream and does not participate in semantic authority

### Partial failure behavior
- any failure before receipt publication aborts promotion
- runtime continues to see the last promoted valid set
- if no promoted set exists yet, `skill_hub` is unavailable rather than downgraded

### Runtime visibility
- runtime may read only the last fully promoted set
- staging input, candidate manifests, failed packs, and partial receipts remain invisible

### Preservation rule
- preserve the last valid promoted set until a newer set is fully admitted
- recovery uses the last promoted set only; no manual artifact surgery

## Admission Checks

### Shape
1. manifest schema version matches canonical contract
2. every canonical entry has stable identity, `relative_path`, and explicit `canonical`
3. pack contains only `doc="skill"` chunks
4. pack ids are all `skill:*`
5. pack excludes `skill.md`, `_ctx/*`, and metadata chunk families

### Provenance
1. promotion request declares `skill_hub`
2. manifest fingerprint is recorded in the promotion receipt
3. pack fingerprint is recorded in the promotion receipt
4. receipt binds segment id, policy, manifest fingerprint, and pack fingerprint

### Closure
1. every canonical manifest entry appears in the pack exactly once
2. no pack chunk exists without a canonical manifest entry
3. every canonical `relative_path` resolves at promotion time
4. derived aliases are generated from the canonical manifest only

### Policy consistency
1. `skill_hub` segments never execute generic build or generic promotion
2. `ContextService` reads only promoted `skill_hub` packs
3. consumers do not read legacy manifest shapes in runtime-critical flows

## Boundary Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Ban legacy pack writer | `scripts/ingest_trifecta.py` is invalid for `skill_hub` from the first governed promotion release | it is a competing writer and breaks single-authority runtime |
| Official replacement entrypoint | governed `trifecta ctx sync --segment <skill-hub>` path backed by `BuildContextPackUseCase` + promotion gate | one operational path, one semantic owner |
| Initial inadmissible live runtime | keep serving the last promoted valid set; if none exists, `skill_hub` stays unavailable | fail closed without manual repair or generic downgrade |
| Aliases migration | `aliases_fs.py` and `cli_skills.py` cut over directly to the canonical manifest contract | avoids dual consumer contracts |
| Alias authority | alias files remain derived convenience artifacts only | derived output must not become a second semantic surface |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/segment_indexing_policy.py` | Modify | Remove any `skill_hub` downgrade semantics. |
| `src/domain/skill_manifest.py` | Modify | Define canonical persisted manifest and admission boundary. |
| `src/application/use_cases.py` | Modify | Make promotion atomic and `skill_hub`-exclusive. |
| `src/application/context_service.py` | Modify | Load only promoted packs. |
| `src/infrastructure/aliases_fs.py` | Modify | Read canonical manifest only. |
| `src/infrastructure/cli_skills.py` | Modify | Consume canonical manifest-derived alias data only. |
| `scripts/ingest_trifecta.py` | Modify | Explicitly reject `skill_hub` usage. |

## Testing Strategy

| Layer | What to Test | Approach |
|------|--------------|----------|
| Unit | manifest normalization and authority invariants | domain tests |
| Integration | promotion transaction, closure checks, partial failure invisibility | use-case tests |
| Acceptance | runtime loads only promoted sets and rejects inadmissible `skill_hub` state | CLI black-box tests |

## Migration / Rollout

1. establish authority boundary, canonicalization, and promotion
2. cut consumers to canonical manifest only
3. remove legacy/external runtime writers from supported paths

Rollback restores the last promoted valid set only.

## Open Questions

- [ ] Which exact naming rule becomes canonical for `source -> relative_path` normalization?
- [ ] What exact receipt schema is required to identify the promoted set without ambiguity?
