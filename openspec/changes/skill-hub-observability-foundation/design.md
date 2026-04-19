# Design: Skill-hub Observability Foundation

## Technical Approach

Introduce a dedicated local-first observability layer for `skill-hub` that records pipeline execution as structured events, rolls those events into a per-run summary, and renders optional diagnostics from that summary. The local event stream becomes the canonical evidence source. Remote vendors remain sinks, never authorities.

The sequence is intentional:
1. **Schema first** — model the pipeline truth.
2. **Local persistence second** — JSONL append-only events + per-run summary.
3. **Diagnostics third** — TTY/plain presentation of the summary.
4. **Remote exporters last** — optional adapters for Sentry/PostHog/OTLP.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Canonical evidence source | Local JSONL + run summary | Cloud backend as primary store | `skill-hub` is a local CLI and must explain failures offline. |
| Observability ownership | Dedicated `skill-hub` runtime observability layer | Reuse generic repo telemetry as-is | Generic telemetry does not model cards/search/promotion semantics with enough fidelity. |
| Diagnostics source | Derived from run summary only | Build directly from ad-hoc logs/print statements | Prevents visible diagnostics from drifting away from persisted evidence. |
| Vendor integration | Opt-in adapters behind a narrow interface | Bake vendor SDKs into runtime core | Keeps local-first guarantee and avoids lock-in or network-coupled failures. |
| UI timing | Status strip / diagnostics after schema is stable | Build rich diagnostic cards first | Data model must exist before presentation or the UI becomes fake certainty. |

## Architecture Shape

```text
skill-hub entrypoint
  -> skill-hub semantic pipeline
      (search -> ranking -> promotion -> renderer route -> render)
  -> observability runtime context
      -> emit structured events
      -> persist append-only JSONL
      -> aggregate run summary
      -> optional diagnostic rendering
      -> optional remote exporters
```

## Runtime Components

### 1. Observability Context
A per-run context owns identifiers and shared metadata:
- `run_id`
- `query_id`
- command/surface
- TTY mode
- schema version
- config/runtime receipt fingerprints when available

This context must be created once near CLI entry and threaded through the runtime pipeline.

### 2. Local Event Sink
Canonical append-only JSONL file, likely under a skill-hub-specific local state path or another explicitly chosen runtime-safe location. Each event records:
- event name
- stage
- timing/duration
- counts
- degradation flags
- reason codes
- safe fingerprints (not raw secrets/PII)

### 3. Run Summary Builder
At the end of a run, the system builds a summary artifact for the run with:
- hits/ranked/promoted/renderable/dropped counts
- drop reasons
- renderer route selected
- config/runtime/receipt health
- slowest steps
- exception/error capture state
- remote sink status (if enabled)

### 4. Diagnostics Renderer
Consumes only the run summary and supports:
- compact status strip
- plain diagnostics
- rich TTY diagnostics/card-style panel

The renderer must not compute business truth. It only formats already-derived state.

### 5. Optional Remote Exporters
Adapters, not authorities:
- `SentrySink` for exceptions + structured technical logs
- `PostHogSink` for usage/product events
- `OtlpSink` for future portability into Axiom/Logfire/Parseable/Grafana ecosystems

## Event Model

Minimum governed event set:
- `cli.invoked`
- `config.loaded`
- `runtime.verified`
- `search.started`
- `search.completed`
- `ranking.completed`
- `promotion.started`
- `promotion.completed`
- `promotion.card_dropped`
- `renderer.route_selected`
- `renderer.completed`
- `diagnostics.summary_built`
- `error.captured`

Required event fields:
- `timestamp`
- `schema_version`
- `run_id`
- `query_id`
- `command`
- `surface`
- `tty_mode`
- `event_name`
- `step`
- `level`
- `duration_ms`
- `counts`
- `reason`
- `config_hash`
- `runtime_receipt_hash`
- `exception_type`

## File Changes

| File | Action | Description |
|---|---|---|
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` | Modify | Emit pipeline events, reason codes, and summary inputs from semantic runtime stages. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py` | Modify | Add diagnostics/status renderers that consume summary data only. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` | Maybe Modify | Pass observability flags/context from main CLI invocation path. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards` | Maybe Modify | Keep cards adapter aligned with summary/diagnostics routing. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/infrastructure/telemetry.py` | Maybe Modify or Reference | Reuse privacy/sanitization patterns if appropriate without conflating generic telemetry with skill-hub domain events. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/` | Modify/Add | Cover event emission, summary derivation, diagnostics rendering, sink isolation, and fail-closed behavior. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/acceptance/` | Modify/Add | Validate observable behavior in real CLI invocations. |

## Interfaces / Contracts

- Semantic ownership remains in existing `skill_hub_cards_core.py` runtime logic.
- Observability records what happened; it does not decide what should happen.
- Diagnostic output is derived from run summaries only.
- Remote sinks must be best-effort and non-fatal.
- Local sink generation must remain available without network access.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | event schema, reason-code emission, summary aggregation | focused pytest on observability helpers and runtime hooks |
| Unit | diagnostics rendering in TTY/plain | focused pytest on runtime UX helpers |
| Integration | CLI writes local artifacts and summaries for real runs | targeted CLI invocation tests |
| Acceptance | `hits != cards` explanation is visible and stable | black-box acceptance flow using representative queries |
| Resilience | remote sink failure stays non-fatal | adapter tests with failing sinks |

## Rollout Strategy

### Phase 1
- local schema
- JSONL sink
- run summary
- no-op remote sink

### Phase 2
- diagnostics/status strip
- plain + rich rendering for summaries

### Phase 3
- Sentry sink
- PostHog sink
- optional OTLP export path

## Open Questions

- [ ] Whether to store skill-hub observability under `_ctx/telemetry`, a tool-specific state root, or another governed local location.
- [ ] Whether diagnostics should default to silent status, opt-in flag, or explicit subcommand first.
- [ ] How much of `src/infrastructure/telemetry.py` should be reused versus duplicated with a narrower skill-hub contract.
