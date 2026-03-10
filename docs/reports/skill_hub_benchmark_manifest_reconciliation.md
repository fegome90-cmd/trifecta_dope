# Benchmark ↔ Manifest Reconciliation for `skill-hub`

## Scope
Reconcile the pilot benchmark expectations against the frozen manifest used in Phase 6.

Frozen inputs referenced:
- `data/skill_hub_pilot_queries.yaml`
- `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`
- Phase 6 rows and raw outputs

## Method
For each hard-positive and ambiguous query:
1. read `expected_good_skills`
2. check whether each expected name exists in the frozen manifest
3. classify as:
   - `exists`
   - `missing`
   - `canonicalized`
   - `invalid expectation`
4. propose a canonical skill candidate only when a reasonable equivalent exists in the manifest or in observed retrieval outputs

## Reconciliation table

| query_id | expected original | status | canonical skill candidate | justification |
|---|---|---:|---|---|
| q01 | methodology-workflows | missing | verification-loop / strategic-compact | No exact manifest entry. Expected intent is methodology/workflow orchestration. Closest existing canons are adjacent operational workflow skills, not a direct replacement. |
| q01 | work-order-workflows | missing | workorder-execution-base / git-worktree-curated | No exact manifest entry. Expected concept exists only indirectly via workorder execution and worktree operations. |
| q01 | tmux-plan-auditor | exists | tmux-plan-auditor | Exact manifest hit. |
| q01 | workorder-execution-base | exists | workorder-execution-base | Exact manifest hit. |
| q01 | strategic-compact | exists | strategic-compact | Exact manifest hit. |
| q02 | methodology-workflows | missing | verification-loop / strategic-compact | Same issue as q01. Benchmark expects a ghost name. |
| q02 | work-order-workflows | missing | workorder-execution-base / git-worktree-curated | Same issue as q01. |
| q02 | tmux-plan-auditor | exists | tmux-plan-auditor | Exact manifest hit. |
| q02 | workorder-execution-base | exists | workorder-execution-base | Exact manifest hit. |
| q03 | tmux-plan-auditor | exists | tmux-plan-auditor | Exact manifest hit. |
| q03 | branch-review-api | exists | branch-review-api | Exact manifest hit. |
| q03 | verification-loop | exists | verification-loop | Exact manifest hit. |
| q05 | debug-helper | exists | debug-helper | Exact manifest hit. |
| q05 | python-testing | exists | python-testing | Exact manifest hit. |
| q05 | tdd-workflow | exists | tdd-workflow | Exact manifest hit. |
| q05 | systematic-debugging (adjacent) | canonicalized | superpowers-systematic-debugging | No canonical manifest entry named `systematic-debugging`; observed surface form is prefixed variant. |
| q05 | root-cause-tracing (adjacent) | missing | none | No exact manifest entry and no convincing surfaced canonical equivalent was found in manifest readout. |
| q09 | branch-review-api | exists | branch-review-api | Exact manifest hit. |
| q09 | github-pr-curated | exists | github-pr-curated | Exact manifest hit. |
| q09 | learned-pr-feedback-resolution | exists | learned-pr-feedback-resolution | Exact manifest hit. |
| q09 | examen-code-review-checklist (adjacent) | missing | branch-review / requesting-code-review | No exact manifest entry. Benchmark used a non-existent surface form. Nearby review-oriented skills do exist but under different names. |
| q12 | methodology-workflows | missing | verification-loop / strategic-compact | Same ghost-name issue as q01/q02. |
| q12 | tmux-plan-auditor | exists | tmux-plan-auditor | Exact manifest hit. |
| q12 | work-order-workflows | missing | workorder-execution-base / git-worktree-curated | Same ghost-name issue as q01/q02. |
| q12 | strategic-compact | exists | strategic-compact | Exact manifest hit. |

## Findings
### R1 — The benchmark still expects ghost names
Ghost expectations confirmed:
- `methodology-workflows`
- `work-order-workflows`
- `root-cause-tracing`
- `examen-code-review-checklist`

These should not remain as primary expected names if the experiment is meant to reflect the real searchable surface of the frozen segment.

### R2 — Some expectations are conceptually valid but need canonicalization
Canonicalization candidates:
- `systematic-debugging` -> `superpowers-systematic-debugging`

This is a naming-surface problem, not a query-intent problem.

### R3 — Hard-positive workflow queries are partially under-specified against the real corpus
Queries `q01`, `q02`, `q12` rely on umbrella workflow names that the real corpus does not expose as canonical searchable entries.

## Decision
The benchmark is **not fully reconciled yet**.

It is usable for diagnosis, but before using it as a post-curation measurement source of truth, these ghost expectations must be handled explicitly.

## Minimal corrective rule
For the next mini-experiments:
- keep existing query text unchanged
- replace ghost expectations with one of:
  - real manifest-backed canonical names, or
  - explicit `adjacent acceptable` names that exist in the manifest
- do not keep non-existent names as primary expected winners

## Recommended benchmark patch set
### Replace / demote ghost expectations
- `methodology-workflows` -> demote; use `verification-loop` and `strategic-compact` as adjacent existing workflow surrogates
- `work-order-workflows` -> demote; use `workorder-execution-base` as primary existing equivalent and `git-worktree-curated` as adjacent operational surrogate
- `systematic-debugging` -> canonicalize to `superpowers-systematic-debugging` unless a canonical visible alias is added later
- `root-cause-tracing` -> remove from expectations until a real manifest-backed visible entry exists
- `examen-code-review-checklist` -> remove from expectations until a real manifest-backed visible entry exists

## Status
**pass with issues**
