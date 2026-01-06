# Backlog Migration

## Source

- `docs/backlog/legacy/inputs/central_telefonica_v0.1.yaml`

## Mapping

- Epic `E-0001` copied into `_ctx/backlog/backlog.yaml`
- `generated_at` preserved, `curated_at` mapped to `x_curated_at`
- `wo_queue` trimmed to existing WOs; full list preserved in `x_legacy_wo_queue`

## Notes

- Source file remains read-only under legacy inputs.
- Work orders are executed from `_ctx/jobs/{pending,running,done,failed}`.
