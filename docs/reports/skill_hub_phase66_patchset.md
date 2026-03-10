# Fase 6.6 — Ola 1 Patch Set for `skill-hub`

## Scope
Convert Ola 1 analysis into a concrete, minimal, reversible, measurable patch set.

This phase does **not**:
- modify Trifecta
- create a parallel system
- touch production
- add aliases
- rewrite SKILL.md content
- run E1 yet

## Inputs used
- `docs/reports/skill_hub_benchmark_manifest_reconciliation.md`
- `docs/reports/skill_hub_benchmark_manifest_reconciliation_operational.md`
- `docs/reports/skill_hub_phase65_metadoc_hygiene.md`
- `docs/reports/skill_hub_phase65_canonicalization_minimal.md`
- `docs/reports/skill_hub_phase65_curation_plan.md`
- `docs/reports/skill_hub_phase6_pilot_run.md`
- `docs/reports/skill_hub_phase6_recovery_postmortem.md`
- `eval/results/skill_hub_phase6/20260309T134513Z/summary.json`
- `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`
- frozen segment artifacts (`skills_manifest.json`, `aliases.yaml`, `context_pack.json`)

---

## Bloque 1 — Benchmark reconciliation operativa
### 1. Qué analicé
- ghost expectations
- canonicalizable expectations
- query-level impact on scoring

### 2. Qué evidencia encontré
Ghost names still blocking clean measurement:
- `methodology-workflows`
- `work-order-workflows`
- `root-cause-tracing`
- `examen-code-review-checklist`

Canonicalizable:
- `systematic-debugging` -> `superpowers-systematic-debugging`

### 3. Qué decisión tomé
- created an operational reconciliation artifact that defines what the benchmark must use before E1
- the benchmark may no longer score against ghost names as primary winners

### 4. Qué no toqué y por qué
- I did not edit `data/skill_hub_pilot_queries.yaml` yet
- operational reconciliation comes first, dataset patch only after this patch set is accepted

### 5. Qué artefactos dejé
- `docs/reports/skill_hub_benchmark_manifest_reconciliation_operational.md`

### 6. Estado
- **pass**

---

## Bloque 2 — Metadoc exclusion plan operable
### 1. Qué analicé
Target contaminants:
- `~/.trifecta/segments/skills-hub/_ctx/prime_skills-hub.md`
- `~/.trifecta/segments/skills-hub/_ctx/agent_skills-hub.md`
- `~/.trifecta/segments/skills-hub/_ctx/session_skills-hub.md`
- `~/.trifecta/segments/skills-hub/AGENTS.md`
- `~/.trifecta/segments/skills-hub/README.md`

Observed retrieval contamination:
- `q02` -> `prime_skills-hub`, `agent_skills-hub`
- `q12` -> `AGENTS.md`

### 2. Qué evidencia encontré
- These files are searchable today via the frozen context pack.
- They are not executable skills; they are docs/config/history.

### 3. Qué decisión tomé
Operational plan:
- **exclude** all five from the main skill search surface
- do not merely degrade them in Ola 1

### 4. Qué no toqué y por qué
- I did not modify `context_pack.json` or source files yet
- first the patch set needs to freeze the exact move

### 5. Qué artefactos dejé
- this patch set document
- `docs/reports/skill_hub_phase65_metadoc_hygiene.md`

### 6. Estado
- **pass**

### Metadoc exclusion matrix
| Target file | Action | File/path to touch | Exact mechanism | Reversible? | Queries expected to improve |
|---|---|---|---|---|---|
| `prime_skills-hub.md` | exclude | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` and source selection used to build that pack | remove from searchable source set for skill surface rebuild | yes: re-add entry to source set and rebuild pack | `q02` |
| `agent_skills-hub.md` (root and `_ctx` variant) | exclude | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` and source selection used to build that pack | remove from searchable source set for skill surface rebuild | yes | `q02` |
| `session_skills-hub.md` (root and `_ctx` variant) | exclude | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` and source selection used to build that pack | remove from searchable source set for skill surface rebuild | yes | vague future workflow queries; indirect protection |
| `AGENTS.md` | exclude | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` and source selection used to build that pack | remove from searchable source set for skill surface rebuild | yes | `q12` |
| `README.md` | exclude | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` and source selection used to build that pack | remove from searchable source set for skill surface rebuild | yes | indirect protection for abstract help/skill queries |

---

## Bloque 3 — Canonicalization plan operable
### 1. Qué analicé
Minimal duplicate/prefix cases with direct Phase 6 evidence.

### 2. Qué evidencia encontré
Highest-priority cases:
- `dispatching-parallel-agents`
- `python-testing`
- `tdd-workflow`
- `strategic-compact`
- `learned-pr-feedback-resolution`
- `branch-review-api` vs `examen-branch-review-api`

### 3. Qué decisión tomé
- Keep canonical visible entries for exact duplicate concepts
- Degrade only the noisy duplicate variants that have strong evidence of contamination
- Do **not** do mass prefix cleanup in Ola 1

### 4. Qué no toqué y por qué
- I did not touch `official-*`, `adr-*`, or broad `plugin-*` families globally
- I did not change SKILL.md content yet

### 5. Qué artefactos dejé
- this patch set document
- `docs/reports/skill_hub_phase65_canonicalization_minimal.md`

### 6. Estado
- **pass with issues**

### Canonicalization matrix
| Case | Canonical visible entry | Degraded duplicate | File/path to touch | Exact mechanism | Reversible? | Queries affected |
|---|---|---|---|---|---|---|
| dispatching parallel agents | `dispatching-parallel-agents` | `examen-dispatching-parallel-agents.md`, `superpowers-dispatching-parallel-agents.md` | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` and searchable corpus entry metadata | introduce one canonical visible manifest entry or canonical display mapping; mark prefixed variants as secondary/non-primary visible duplicates | yes | `q01` |
| python testing | `python-testing` | duplicate source variant of `python-testing.md` | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | select one canonical visible entry, mark second as duplicate secondary | yes | protects controls and test-related retrieval consistency |
| tdd workflow | `tdd-workflow` | duplicate source variant of `tdd-workflow.md` | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | same as above | yes | `q04`, `q05` stability |
| strategic compact | `strategic-compact` | duplicate source variant of `strategic-compact.md` | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | same as above | yes | `q01`, `q02`, `q12` |
| learned PR feedback | `learned-pr-feedback-resolution` | duplicate source variant of same name | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | same as above | yes | `q09` |
| branch review API | `branch-review-api.md` | `examen-branch-review-api.md` | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` and searchable corpus metadata | canonicalize visible entry to non-prefixed branch-review API; mark examen variant as secondary duplicate | yes | `q08`, `q09` |

---

## Bloque 4 — Patch set mínimo final
### 1. Qué analicé
- the smallest set of reversible changes that make Ola 1 measurable

### 2. Qué evidencia encontré
- without operational benchmark reconciliation, E1 cannot be interpreted cleanly
- without metadoc exclusion, q02/q12 stay confounded
- without minimal canonicalization, prefix noise remains hard to interpret

### 3. Qué decisión tomé
- define a minimal patch set to apply **before** E1

### 4. Qué no toqué y por qué
- no aliases
- no SKILL.md edits
- no rerun

### 5. Qué artefactos dejé
- this patch set document

### 6. Estado
- **pass**

### Patch set table
| patch_id | artifact_to_change | exact_change | expected_effect | rollback | risk |
|---|---|---|---|---|---|
| P66-01 | `data/skill_hub_pilot_queries.yaml` | replace ghost expectations using `docs/reports/skill_hub_benchmark_manifest_reconciliation_operational.md`; remove invalid primary expectations | benchmark becomes manifest-backed and measurable | restore previous dataset file from frozen hash/version | medium: changes evaluation contract, must be documented clearly |
| P66-02 | `~/.trifecta/segments/skills-hub/_ctx/context_pack.json` plus source selection feeding it | exclude `prime_skills-hub.md`, `agent_skills-hub.md`, `session_skills-hub.md`, `AGENTS.md`, `README.md` from main skill search surface | reduce metadoc contamination in `q02`, `q12` | re-add files to source set and rebuild/search pack | medium: requires careful rebuild discipline |
| P66-03 | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` | mark canonical visible entries and duplicate-secondary entries for exact duplicates (`python-testing`, `tdd-workflow`, `strategic-compact`, `learned-pr-feedback-resolution`) | reduce duplicate/source noise without broad renaming | revert manifest patch | low |
| P66-04 | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` and searchable entry metadata | canonicalize branch review surface to `branch-review-api`, demote `examen-branch-review-api` as secondary | improve review-related surface coherence | revert manifest/metadata patch | medium |
| P66-05 | `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` and searchable entry metadata | add one canonical visible surface for `dispatching-parallel-agents`, demote prefixed duplicates | reduce source-label noise for agent-parallelism related retrieval | revert manifest/metadata patch | medium |

---

## Lista exacta de archivos a tocar en Ola 1
### Benchmark / evaluation
- `data/skill_hub_pilot_queries.yaml`
- `docs/reports/skill_hub_benchmark_manifest_reconciliation_operational.md` (already produced; source of truth for patch)

### Search surface / metadoc hygiene
- `~/.trifecta/segments/skills-hub/_ctx/context_pack.json`
- source-selection inputs that currently feed these searchable docs:
  - `~/.trifecta/segments/skills-hub/_ctx/prime_skills-hub.md`
  - `~/.trifecta/segments/skills-hub/_ctx/agent_skills-hub.md`
  - `~/.trifecta/segments/skills-hub/_ctx/session_skills-hub.md`
  - `~/.trifecta/segments/skills-hub/AGENTS.md`
  - `~/.trifecta/segments/skills-hub/README.md`
  - `~/.trifecta/segments/skills-hub/agent_skills-hub.md`
  - `~/.trifecta/segments/skills-hub/session_skills-hub.md`

### Canonicalization / duplicate metadata
- `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`
- visible/searchable corpus entries involved in canonical surface selection:
  - `~/.trifecta/segments/skills-hub/branch-review-api.md`
  - `~/.trifecta/segments/skills-hub/examen-branch-review-api.md`
  - `~/.trifecta/segments/skills-hub/examen-dispatching-parallel-agents.md`
  - `~/.trifecta/segments/skills-hub/superpowers-dispatching-parallel-agents.md`
  - `~/.trifecta/segments/skills-hub/python-testing.md`
  - `~/.trifecta/segments/skills-hub/tdd-workflow.md`
  - `~/.trifecta/segments/skills-hub/strategic-compact.md`
  - `~/.trifecta/segments/skills-hub/learned-pr-feedback-resolution.md`

---

## Gate final
### Is Ola 1 ready to be applied?
**Yes, with one pre-application condition:**
- the operational benchmark reconciliation must be accepted as the evaluation contract for E1

### What still blocks E1?
Open blockers before E1:
1. apply the benchmark patch so E1 does not score against ghost names
2. ensure the metadoc exclusion mechanism is representable cleanly in the segment build/search surface without touching Trifecta
3. ensure canonicalization is represented as metadata/search-surface curation, not as engine logic

If those three are satisfied, Ola 1 is ready to apply and E1 can be prepared next.

## Status
**pass with issues**
