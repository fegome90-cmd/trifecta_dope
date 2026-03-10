# Benchmark ↔ Manifest Reconciliation — Operational Artifact

## Purpose
Convert the analytical reconciliation into an operational benchmark patch contract for Ola 1.

This artifact defines, per affected query, the benchmark expectation state that must be used before E1 is allowed to run.

## Rules
- Query text stays unchanged.
- Non-existent names cannot remain as primary expected winners.
- A `canonical expected` must be manifest-backed.
- `invalid expectation` means remove from primary expectations until a real manifest-backed canonical visible entry exists.

## Operational reconciliation table

| query_id | expected original | canonical expected | status | impact on evaluation |
|---|---|---|---|---|
| q01 | methodology-workflows | verification-loop / strategic-compact | invalid expectation | Remove as primary expected winner. Keep only as conceptual note outside scoring. |
| q01 | work-order-workflows | workorder-execution-base / git-worktree-curated | invalid expectation | Remove as primary expected winner. Use real manifest-backed work-order skills for scoring. |
| q01 | tmux-plan-auditor | tmux-plan-auditor | exists | No scoring change. |
| q01 | workorder-execution-base | workorder-execution-base | exists | No scoring change. |
| q01 | strategic-compact | strategic-compact | exists | No scoring change. |
| q02 | methodology-workflows | verification-loop / strategic-compact | invalid expectation | Remove as primary expected winner. |
| q02 | work-order-workflows | workorder-execution-base / git-worktree-curated | invalid expectation | Remove as primary expected winner. |
| q02 | tmux-plan-auditor | tmux-plan-auditor | exists | No scoring change. |
| q02 | workorder-execution-base | workorder-execution-base | exists | No scoring change. |
| q05 | debug-helper | debug-helper | exists | No scoring change. |
| q05 | python-testing | python-testing | exists | No scoring change. |
| q05 | tdd-workflow | tdd-workflow | exists | No scoring change. |
| q05 | systematic-debugging | superpowers-systematic-debugging | canonicalized | Replace adjacent expected with manifest-backed visible form for scoring until a cleaner canonical visible alias exists. |
| q05 | root-cause-tracing | none | invalid expectation | Remove from expectations until a real manifest-backed visible entry exists. |
| q09 | branch-review-api | branch-review-api | exists | No scoring change. |
| q09 | github-pr-curated | github-pr-curated | exists | No scoring change. |
| q09 | learned-pr-feedback-resolution | learned-pr-feedback-resolution | exists | No scoring change. |
| q09 | examen-code-review-checklist | none | invalid expectation | Remove from adjacent acceptable list until a real manifest-backed visible entry exists. |
| q12 | methodology-workflows | verification-loop / strategic-compact | invalid expectation | Remove as primary expected winner. |
| q12 | work-order-workflows | workorder-execution-base / git-worktree-curated | invalid expectation | Remove as primary expected winner. |
| q12 | tmux-plan-auditor | tmux-plan-auditor | exists | No scoring change. |
| q12 | strategic-compact | strategic-compact | exists | No scoring change. |

## Query-level summary

### q01
- Primary expected winners allowed after reconciliation:
  - `tmux-plan-auditor`
  - `workorder-execution-base`
  - `strategic-compact`
- Adjacent acceptable allowed:
  - `verification-loop`
  - `git-worktree-curated`
- Removed from primary expectations:
  - `methodology-workflows`
  - `work-order-workflows`

### q02
- Primary expected winners allowed after reconciliation:
  - `tmux-plan-auditor`
  - `workorder-execution-base`
- Adjacent acceptable allowed:
  - `strategic-compact`
  - `verification-loop`
  - `git-worktree-curated`
- Removed from primary expectations:
  - `methodology-workflows`
  - `work-order-workflows`

### q05
- Primary expected winners allowed after reconciliation:
  - `debug-helper`
  - `python-testing`
  - `tdd-workflow`
- Adjacent acceptable allowed:
  - `superpowers-systematic-debugging`
- Removed from expectations:
  - `root-cause-tracing`

### q09
- Primary expected winners allowed after reconciliation:
  - `branch-review-api`
  - `github-pr-curated`
  - `learned-pr-feedback-resolution`
- Adjacent acceptable allowed:
  - `verification-loop`
- Removed from adjacent expectations:
  - `examen-code-review-checklist`

### q12
- Primary expected winners allowed after reconciliation:
  - `tmux-plan-auditor`
  - `strategic-compact`
- Adjacent acceptable allowed:
  - `workorder-execution-base`
  - `verification-loop`
  - `git-worktree-curated`
- Removed from primary expectations:
  - `methodology-workflows`
  - `work-order-workflows`

## Gate
E1 must not run until the benchmark used by the experiment reflects this operational reconciliation.

## Status
**pass**
