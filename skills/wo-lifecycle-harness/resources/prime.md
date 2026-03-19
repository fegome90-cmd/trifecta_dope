# Prime — WO Lifecycle Harness

## Anchor

- `docs/plans/WO-LIFECYCLE-HARNESS-ANCHOR.md`

## Key Normative Docs

- `docs/backlog/MANUAL_WO.md`
- `docs/backlog/WORKFLOW.md`
- `docs/backlog/OPERATIONS.md`
- `docs/backlog/ADR-001-finish-gate-policy.md`

## Relevant Official Scripts

- `scripts/ctx_wo_preflight.py`
- `scripts/ctx_wo_take.py`
- `scripts/ctx_wo_finish.py`
- `scripts/ctx_wo_requeue.py`

## Key Controlled / Transitional Surfaces

- `scripts/ctx_verify_run.sh`
- `scripts/wo_verify.sh`
- `scripts/verify.sh`
- `scripts/repo_verify.sh`
- `scripts/ctx_verify_wo.py`
- `scripts/ctx_reconcile_state.py`
- `scripts/ctx_wo_gc.py`
- `scripts/wo_audit.py`

## Key Contract Tests

- `tests/unit/test_wo_finish_cli.py`
- `tests/unit/test_wo_finish_requires_evidence.py`
- `tests/integration/test_wo_closure.py`
- `tests/integration/test_wo_crash_safety.py`
