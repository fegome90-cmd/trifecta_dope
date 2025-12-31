# Ambiguous + Multi-hop Spec

Goal: test retrieval across multiple relevant docs for ambiguous prompts.

Expected sources (top-5, per query):
- roadmap v2 + action plan: `docs/v2_roadmap/roadmap_v2.md` and
  `docs/plans/2025-12-30_action_plan_v1.1.md`
- context-pack ingestion vs implementation: `docs/plans/2025-12-29-context-pack-ingestion.md` and
  `docs/implementation/context-pack-implementation.md`
- context loading vs implementation workflow: `docs/plans/2025-12-29-trifecta-context-loading.md` and
  `docs/plans/2025-12-30_implementation_workflow.md`
- telemetry plan vs telemetry analysis: `docs/plans/2025-12-31_telemetry_data_science_plan.md` and
  `docs/data/2025-12-30_telemetry_analysis.md`
- roadmap priorities vs research roi matrix: `docs/v2_roadmap/roadmap_v2.md` and
  `docs/v2_roadmap/research_roi_matrix.md`

Pass criteria:
- 4/5 queries have `minirag-eval/bridges/all_bridges.md` in top-5.
