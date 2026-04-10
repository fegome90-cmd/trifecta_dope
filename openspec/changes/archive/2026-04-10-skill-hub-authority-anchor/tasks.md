# Tasks: Skill-hub Authority Anchor

## Scope

- Materialize the governed `skill_hub` authority model already fixed by `proposal.md`, `design.md`, and `spec.md`.
- Establish one promotion boundary, one canonical manifest surface, one promoted artifact set, one runtime load rule, and one downstream consumer contract.
- Deliver implementation work in dependency order so runtime authority is never split during execution.

## Non-goals

- Re-deciding policy, authority, or runtime semantics already closed in design/spec.
- Reindexing or repairing the current live `skills-hub` segment by hand.
- Introducing a second system, alternate runtime path, or generic fallback for `skill_hub`.
- Leaving any runtime-critical consumer on the legacy manifest contract after cutover.

## Execution invariants

- `skill_hub` segments MUST NOT fall back to `generic`.
- No parallel writers may exist for canonical manifest or promoted pack.
- Runtime MUST consume only a valid promoted artifact set.
- Manual state surgery is prohibited.
- Legacy compatibility exists only at the admission boundary.
- Derived aliases are convenience output only and are never authority.
- After downstream cutover, no runtime-critical consumer may read the legacy manifest contract.
- Evidence is not authority; receipts prove promotion but do not replace canonical artifacts.

## Epics / workstreams

### Epic 1 — Promotion boundary

- [x] **1.1 Govern the official `skill_hub` promotion entrypoint**
  - **Objective**: Make `trifecta ctx sync --segment <skill-hub>` the only supported path that can publish `skill_hub` runtime state.
  - **Surfaces touched**: promotion transaction, runtime load surface, policy consistency.
  - **Authoritative artifacts affected**: canonical manifest, promoted pack, promotion receipt.
  - **Changes explicitly prohibited**: generic fallback, alternate writer paths, manual promotion shortcuts.
  - **Dependencies**: none.
  - **Acceptance criteria**: one governed path exists for `skill_hub` promotion and design/spec decisions remain unchanged.
  - **Rollback / compensation**: restore prior Trifecta orchestration code only; do not reopen external runtime writers.
  - **Expected evidence or tests**: integration test proving `skill_hub` promotion calls the governed path only.

- [x] **1.2 Make `skill_hub` fail closed at the policy boundary**
  - **Objective**: Remove any effective downgrade path from declared `skill_hub` segments to generic behavior.
  - **Surfaces touched**: policy consistency, promotion transaction.
  - **Authoritative artifacts affected**: none directly; governs all promoted artifacts.
  - **Changes explicitly prohibited**: silent downgrade, query-time repair, shadow runtime path.
  - **Dependencies**: 1.1.
  - **Acceptance criteria**: declared `skill_hub` with invalid state fails hard before promotion.
  - **Rollback / compensation**: revert the policy guard without changing artifact ownership.
  - **Expected evidence or tests**: unit/integration tests for declared `skill_hub` + invalid inputs => failure, not generic.

### Epic 2 — Canonical manifest persistence

- [x] **2.1 Implement canonical manifest normalization and persistence**
  - **Objective**: Convert staging input into the only persisted canonical manifest contract.
  - **Surfaces touched**: upstream manifest input, canonical normalized manifest.
  - **Authoritative artifacts affected**: `_ctx/skills_manifest.json`.
  - **Changes explicitly prohibited**: dual manifest writers, legacy manifest as runtime truth.
  - **Dependencies**: 1.1, 1.2.
  - **Acceptance criteria**: only canonical schema persists for `skill_hub`; staging input remains non-authoritative.
  - **Rollback / compensation**: keep previous admitted canonical manifest; never expose staging input directly.
  - **Expected evidence or tests**: domain tests for normalization, rejection of malformed/stale staging input.

- [x] **2.2 Encode manifest admission checks**
  - **Objective**: enforce the closed Shape / Provenance / Closure / Policy consistency checks before pack build.
  - **Surfaces touched**: canonical normalized manifest, promotion transaction.
  - **Authoritative artifacts affected**: canonical manifest candidate.
  - **Changes explicitly prohibited**: vague “best effort” validation, partial acceptance.
  - **Dependencies**: 2.1.
  - **Acceptance criteria**: each admission rule from design/spec is executable as a gate or test.
  - **Rollback / compensation**: revert only the new checks as a unit; keep single manifest authority intact.
  - **Expected evidence or tests**: unit/integration tests per check group with explicit pass/fail cases.

### Epic 3 — Promoted set sealing

- [x] **3.1 Implement atomic promoted artifact set publication**
  - **Objective**: publish canonical manifest, canonical pack, and promotion receipt as one all-or-nothing set.
  - **Surfaces touched**: skill_hub context pack, promotion transaction / promoted artifact set, admission receipt.
  - **Authoritative artifacts affected**: `_ctx/skills_manifest.json`, `_ctx/context_pack.json`, promotion receipt.
  - **Changes explicitly prohibited**: exposing partial writes, promoting manifest without matching pack, pack without receipt.
  - **Dependencies**: 2.1, 2.2.
  - **Acceptance criteria**: runtime can never observe a new manifest with an old pack or vice versa.
  - **Rollback / compensation**: preserve and continue serving the last promoted valid set.
  - **Expected evidence or tests**: integration tests for atomic visibility and no partial promotion.

- [x] **3.2 Seal provenance and preserve last valid promoted set**
  - **Objective**: bind manifest fingerprint, pack fingerprint, segment id, and policy into the receipt and preserve the previous valid set until the new one is complete.
  - **Surfaces touched**: promotion transaction, admission receipt, runtime load surface.
  - **Authoritative artifacts affected**: promotion receipt, last promoted set pointer/state.
  - **Changes explicitly prohibited**: unsealed runtime visibility, manual rollback by artifact editing.
  - **Dependencies**: 3.1.
  - **Acceptance criteria**: failed promotion leaves last promoted set active; unsealed set is invisible.
  - **Rollback / compensation**: revert to last promoted valid set via governed pointer only.
  - **Expected evidence or tests**: integration tests for partial failure invisibility and preserved prior set.

### Epic 4 — Runtime gating

- [x] **4.1 Gate `ContextService` and runtime callers to promoted sets only**
  - **Objective**: make runtime consumption fail closed unless a valid promoted set exists.
  - **Surfaces touched**: runtime load surface, policy consistency.
  - **Authoritative artifacts affected**: promoted pack + receipt.
  - **Changes explicitly prohibited**: loading candidate/unsealed packs, generic query path for `skill_hub`.
  - **Dependencies**: 3.1, 3.2.
  - **Acceptance criteria**: runtime reads only promoted sets; invalid live state is unavailable, not repaired.
  - **Rollback / compensation**: restore previous runtime gate while keeping promoted set semantics.
  - **Expected evidence or tests**: acceptance tests for runtime rejection of inadmissible `skill_hub` state.

- [x] **4.2 Handle initial inadmissible live runtime without manual surgery**
  - **Objective**: codify startup behavior when the current runtime state does not satisfy admission.
  - **Surfaces touched**: runtime load surface, promotion transaction.
  - **Authoritative artifacts affected**: currently promoted set pointer/state.
  - **Changes explicitly prohibited**: manual artifact edits, emergency generic fallback.
  - **Dependencies**: 4.1.
  - **Acceptance criteria**: if no valid promoted set exists, `skill_hub` is unavailable by design.
  - **Rollback / compensation**: publish a new valid promoted set through the governed path only.
  - **Expected evidence or tests**: acceptance tests for “no valid promoted set” and “last valid promoted set exists”.

### Epic 5 — Aliases cutover

- [x] **5.1 Cut `aliases_fs.py` over to the canonical manifest contract**
  - **Objective**: remove runtime-critical legacy manifest reads from alias infrastructure.
  - **Surfaces touched**: aliases / CLI consumption surface, canonical normalized manifest.
  - **Authoritative artifacts affected**: canonical manifest; derived alias files downstream only.
  - **Changes explicitly prohibited**: consumer dual contract, legacy `source_path` runtime reads.
  - **Dependencies**: 2.1, 2.2, 3.1.
  - **Acceptance criteria**: alias infrastructure reads only canonical manifest semantics.
  - **Rollback / compensation**: revert alias consumer code only; do not re-authorize legacy manifest.
  - **Expected evidence or tests**: consumer tests on canonical fixtures; failure on legacy-only manifest shape.

- [x] **5.2 Cut `cli_skills.py` over without creating a new semantic surface**
  - **Objective**: keep CLI behavior downstream of canonical manifest + derived aliases only.
  - **Surfaces touched**: aliases / CLI consumption surface.
  - **Authoritative artifacts affected**: canonical manifest; alias outputs remain non-authoritative.
  - **Changes explicitly prohibited**: direct semantic reliance on aliases, side-channel reads from entry files.
  - **Dependencies**: 5.1.
  - **Acceptance criteria**: CLI expansion works, but canonical manifest remains the sole semantic source.
  - **Rollback / compensation**: revert CLI consumer changes; do not keep mixed consumer contracts.
  - **Expected evidence or tests**: tests proving aliases are convenience output and cannot override manifest truth.

### Epic 6 — Legacy writer shutdown

- [x] **6.1 Prohibit `scripts/ingest_trifecta.py` for `skill_hub`**
  - **Objective**: remove the legacy direct pack writer from the supported `skill_hub` runtime path.
  - **Surfaces touched**: skill_hub context pack, policy consistency.
  - **Authoritative artifacts affected**: promoted pack path/rules.
  - **Changes explicitly prohibited**: legacy writer use for `skill_hub`, silent no-op ban.
  - **Dependencies**: 4.1.
  - **Acceptance criteria**: legacy writer is explicitly rejected for `skill_hub` while generic segments remain unaffected.
  - **Rollback / compensation**: revert rejection logic only if it preserves single-authority runtime.
  - **Expected evidence or tests**: tests/docs showing rejection on `skill_hub` use.

- [x] **6.2 Remove external manifest writers from the runtime support path**
  - **Objective**: keep external tooling as staging/audit only, never runtime authority.
  - **Surfaces touched**: upstream manifest input, canonical normalized manifest, promotion transaction.
  - **Authoritative artifacts affected**: canonical manifest, promotion receipt.
  - **Changes explicitly prohibited**: reintroducing shared authority, runtime coexistence with external writes.
  - **Dependencies**: 2.1, 3.1, 5.2, 6.1.
  - **Acceptance criteria**: external tools can feed staging input or audit, but cannot publish runtime state.
  - **Rollback / compensation**: restore Trifecta-governed admission only; never reopen external runtime writers.
  - **Expected evidence or tests**: docs + integration tests proving one writer per runtime surface.

## Dependency order

1. **Phase A (PASS required)**: Epic 1 → Epic 2
   - Blocks all later work until promotion boundary and canonical manifest admission exist.
   - **Inadmissible to advance** if `skill_hub` can still degrade to `generic` or if canonical manifest persistence is not exclusive.

2. **Phase B (PASS required)**: Epic 3
   - Requires Epics 1–2 complete.
   - **Inadmissible to advance** if manifest/pack/receipt cannot be published atomically or if last valid promoted set is not preserved.

3. **Phase C (PASS required)**: Epic 4
   - Requires Epic 3 complete.
   - **Inadmissible to advance** if runtime can still read unsealed/candidate artifacts or if invalid `skill_hub` state can still execute.

4. **Phase D (PASS required)**: Epic 5
   - Requires Epics 2–4 complete.
   - **Inadmissible to advance** if any runtime-critical consumer still reads the legacy contract or if aliases can act as semantic authority.

5. **Phase E (final PASS)**: Epic 6
   - Requires Epics 3–5 complete.
   - **Inadmissible to close the change** if legacy/external writers can still publish `skill_hub` runtime state.

## Acceptance gates by phase

- **Gate A — Authority boundary PASS**
  - `skill_hub` has no generic fallback.
  - canonical manifest is the only persisted manifest authority.

- **Gate B — Promotion PASS**
  - promoted artifact set is atomic, sealed, and preserves the last valid set.

- **Gate C — Runtime PASS**
  - runtime consumes only promoted sets and fails closed otherwise.

- **Gate D — Consumer PASS**
  - `aliases_fs.py` and `cli_skills.py` consume canonical manifest semantics only.
  - derived aliases remain non-authoritative.

- **Gate E — Shutdown PASS**
  - `scripts/ingest_trifecta.py` is invalid for `skill_hub`.
  - external writers cannot publish runtime state.
