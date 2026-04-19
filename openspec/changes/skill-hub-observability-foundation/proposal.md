# Proposal: skill-hub observability foundation

## Intent
Establish a local-first observability foundation for `skill-hub` so every run can explain search, ranking, promotion, renderer routing, configuration health, and runtime receipt status without depending on any remote vendor.

## Scope
### In Scope
- Define a governed local event schema for `skill-hub` runtime execution.
- Add canonical local sinks for append-only JSONL events and per-run summaries.
- Support terminal-facing diagnostics derived from local observability state.
- Keep remote observability integrations opt-in and non-authoritative.
- Reuse existing Trifecta telemetry discipline where it helps, without forcing `skill-hub` to depend on generic telemetry semantics that do not model the cards pipeline.

### Out of Scope
- Full cloud observability rollout.
- Product analytics dashboards.
- Alerting, SLOs, or distributed production infrastructure.
- Replacing the current Trifecta telemetry subsystem globally.
- Reworking search ranking or card promotion semantics themselves.

## Capabilities
### New Capabilities
- `skill-hub` runtime emits structured local observability events for its execution pipeline.
- `skill-hub` can build a run summary that explains counts, drop reasons, degradation, and renderer path.
- Diagnostic output can be rendered from the local run summary in TTY and plain-safe modes.

### Modified Capabilities
- `skill-hub-authority`: runtime execution becomes explainable through governed local observability artifacts without changing semantic authority boundaries.

## Approach
Treat observability as a foundation layer, not as a vendor selection exercise:
1. Define domain-specific runtime events for `skill-hub` pipeline stages.
2. Persist those events locally as the canonical source of truth.
3. Build run summaries and diagnostics from that local data.
4. Add remote sinks only as optional consumers:
   - Sentry for errors + correlated structured logs
   - PostHog for usage/product analytics
   - OpenTelemetry export path for future portability
5. Keep CLI behavior fail-closed if optional remote sinks are unavailable.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `scripts/skill_hub_cards_core.py` | Likely Modified | Emit governed pipeline events and surface summary-relevant counts/reasons. |
| `scripts/skill_hub_runtime_ux.py` | Likely Modified | Render diagnostic/status output from structured summaries without taking semantic authority. |
| `scripts/skill-hub` / `scripts/skill-hub-cards` | Possibly Modified | Thread run context and diagnostics flags through runtime entry points. |
| `src/infrastructure/telemetry.py` | Possibly Referenced / Maybe Extended | Reuse patterns or shared helpers carefully without coupling `skill-hub` to generic telemetry contracts that do not fit. |
| `tests/unit/test_skill_hub_*` | Likely Modified | Cover event schema, summary generation, diagnostics rendering, and fail-closed remote sink behavior. |
| `tests/acceptance/` | Likely Modified | Prove diagnostic output and local artifact generation in real CLI flows. |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Observability becomes another hidden semantic authority | Med | Keep JSONL/summary descriptive only; semantic outcomes remain owned by existing runtime pipeline. |
| Vendor SDKs leak into core runtime and break local-first guarantees | Med | Isolate remote sinks behind adapters and keep local sink mandatory. |
| Diagnostic UI gets built before data model is stable | Med | Sequence work: schema -> local sink -> summary -> UI. |
| Existing Trifecta telemetry and skill-hub observability drift apart confusingly | Med | Define explicit boundary between generic repo telemetry and skill-hub pipeline observability. |

## Rollback Plan
If the observability foundation regresses runtime stability, keep the local schema and sink work behind explicit runtime flags and revert visible diagnostics while preserving the current `skill-hub` user-facing search/card behavior.

## Dependencies
- Existing skill-hub semantic pipeline in `scripts/skill_hub_cards_core.py`
- Existing promoted runtime UX surface in `scripts/skill_hub_runtime_ux.py`
- Existing Trifecta telemetry patterns and privacy constraints in `src/infrastructure/telemetry.py`
- Existing skill-hub promotion/verification contract when runtime artifacts expand

## Success Criteria
- [ ] A real `skill-hub` run can explain `hits != cards` using local summary data.
- [ ] Diagnostics work offline and do not require vendor credentials.
- [ ] Optional remote sink failure does not break CLI execution or local artifacts.
- [ ] TTY/plain diagnostic output remains presentation-only and does not take semantic ownership.
