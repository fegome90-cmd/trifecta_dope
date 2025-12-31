# Temporal + Recency Spec

Goal: check if top results include the most recent doc for a topic.

Expected sources (top-5):
- latest telemetry plan: `docs/plans/2025-12-31_telemetry_data_science_plan.md`
- latest roadmap update: `docs/v2_roadmap/2025-12-31-north-star-validation.md`
- most recent context pack plan: `docs/plans/2025-12-30_implementation_workflow.md`
- latest implementation workflow: `docs/plans/2025-12-30_implementation_workflow.md`
- latest context loading plan: `docs/plans/2025-12-29-trifecta-context-loading.md`

Pass criteria:
- 4/5 queries include one of:
  - expected latest doc in top-5, or
  - `minirag-eval/bridges/all_bridges.md` in top-5.
