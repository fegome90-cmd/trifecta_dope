# Design: Skill-hub Default Path Origin Doctor

## Technical Approach

Keep one CLI contract and one promotion contract.

- **CLI semantic authority**: repo-owned `scripts/skill_hub_cards_core.py` plus the spec in `openspec/changes/skill-hub-default-path-origin-doctor/specs/skill-hub-authority/spec.md`.
- **Runtime publication authority**: `scripts/skill-hub-runtime` is the only writer allowed to promote `~/.local/bin`.
- **Installed runtime status**: `~/.local/bin` is consumable runtime only, never semantic authority.

Current evidence shows drift already exists: `scripts/skill-hub-runtime verify` fails because the receipt records only `skill-hub` and `skill-hub-cards`, while canonical artifacts now also require `skill_hub_runtime_ux.py`. That means installed runtime must fail closed until the promoted set is complete again.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| CLI contract authority | `scripts/skill-hub` is a thin router; admitted query semantics live in `scripts/skill_hub_cards_core.py` | Let wrapper shell parsing define behavior; let cards wrapper define its own rules | Shell glue is operational, not semantic. One semantic engine avoids split-brain. |
| Promotion owner | Only `scripts/skill-hub-runtime` may publish into `~/.local/bin` and receipt storage | Manual copy to `~/.local/bin`; repo scripts self-promoting ad hoc | Promotion is a transaction. One writer is how you prevent local chaos, loco. |
| Repo vs installed runtime | Repo `scripts/` is SSOT; installed files must byte-match the governed promoted set + receipt | Treat installed runtime as “latest wins” | Installed runtime is delivery target, not source of truth. Evidence != authority. |
| `--cards` semantics | Parse argv into one normalized command model before route selection; route depends on mode flag presence, not position | Positional shell branch (`if first arg == --cards`) | Order-independent admission satisfies spec without creating a second authority. |
| Default vs cards paths | Shared semantic admission/query pipeline, separate presentation route only | Two wrappers with independent search/query handling | One semantic contract, two renderers. Same meaning, different output shape. |
| Drift handling | Runtime verify failure blocks authority and surfaces explicit stale/incomplete runtime error | Silent fallback to repo scripts or legacy prose | Fail closed preserves trust and exposes the real defect. |

## Data Flow

```text
user argv
  -> scripts/skill-hub
     -> normalize flags/query once
     -> mode=default | cards
     -> if cards: scripts/skill-hub-cards -> skill_hub_cards_core.py
     -> if default: repo-owned default presenter + same admitted query contract
repo scripts
  -> scripts/skill-hub-runtime promote
  -> atomic copy to ~/.local/bin + receipt write
runtime use
  -> scripts/skill-hub-runtime verify
  -> only complete receipt-bound set is executable authority
```

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/skill-hub-default-path-origin-doctor/design.md` | Create | Document single-authority CLI/promotion design for this change. |
| `scripts/skill-hub` | Future Modify | Normalize argv once, keep wrapper non-authoritative, route default/cards from one command model. |
| `scripts/skill-hub-cards` | Future Modify | Remain runtime adapter only; no independent admission semantics. |
| `scripts/skill_hub_cards_core.py` | Future Modify | Remain semantic authority for query admission/classification. |
| `scripts/skill-hub-runtime` | Future Modify | Enforce complete promoted artifact set and stale runtime detection. |
| `scripts/skill_hub_runtime_ux.py` | Future Modify | Serve both default-path framing and cards framing under presentation-only semantics. |
| `~/.local/bin/skill-hub*` | Runtime Target | Read-only delivery target populated only by governed promotion. |

## Interfaces / Contracts

- `scripts/skill-hub-runtime verify` is the installed-runtime doctor gate.
- Receipt + canonical artifact map define completeness.
- Default path and cards path both consume the same normalized `{query, mode, limit}` command contract.
- Presentation helpers may change copy, but they MUST NOT change admission, routing, or classification semantics.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | argv normalization, shared route contract, receipt completeness rules | pytest over wrapper/runtime helpers |
| Integration | promote/verify detects missing UX artifact and byte drift | pytest around `scripts/skill-hub-runtime` |
| Acceptance | `skill-hub "q" --cards` equals `skill-hub --cards "q"`; drifted runtime fails closed | black-box CLI tests |

## Migration / Rollout

No data migration. Rollout is: fix repo contract -> promote full artifact set atomically -> verify receipt-bound runtime -> only then trust `~/.local/bin` again.

## Open Questions

- [x] Default-path presentation ownership is closed: `scripts/skill_hub_runtime_ux.py` is the only authorized writer for default-path intro/render. `scripts/skill-hub` may invoke that presenter as a thin router, but it MUST NOT print or compose any independent banner, guidance, or alternate render surface of its own.


## Post-Verify External Diagnosis

This change did not close cleanly at `sdd-verify` because the implementation was materially ahead of the verification evidence contract. From an external architecture perspective, the failure was not "the code is broken"; it was "the verification surface and the implementation surface are not yet equally complete."

### Why the SDD cycle did not complete

1. **Implementation outran acceptance-level proof**
   - The owned runtime and wrapper slice now passes focused unit verification.
   - But the spec still contains a promoted-runtime scenario for governed default-path intro/render that was not proven with a dedicated promoted-runtime behavior test.
   - Result: implementation evidence exists, but one spec scenario remains behaviorally under-proven.

2. **Strict-TDD workflow evidence was treated as optional support instead of required contract output**
   - `apply-progress.md` recorded commands and outcomes, but not the stricter TDD-cycle evidence expected by verify.
   - Result: the code may be correct, yet the SDD lifecycle still reports REVIEW because the process artifact is incomplete.

3. **Tasks mixed "behavior proven" with "artifact explicitly produced"**
   - Task `1.2` asks for acceptance coverage specifically.
   - Task `4.3` asks for an explicit planning-gate rerun artifact.
   - Focused unit/runtime checks covered much of the behavior, but they did not satisfy those two artifact-shaped tasks.
   - Result: the cycle remained open even though much of the runtime contract is already working.

4. **Evidence and authority were still slightly misaligned at verify time**
   - Runtime behavior, wrapper smoke checks, and focused test slices provide strong evidence.
   - But SDD verify treats spec scenarios, task completion, and strict-TDD artifacts as authority for archive-readiness.
   - Result: strong evidence was not enough to overrule missing authoritative proof points.

### Critical warning root causes

| Warning class | Root cause | Architectural meaning |
|---|---|---|
| Strict-TDD artifact incomplete | `apply-progress.md` lacks explicit TDD-cycle evidence table/trace | process contract drift |
| Promoted default-path scenario untested | no dedicated promoted-runtime black-box proof for default-path governed intro parity | verification surface gap |
| Task `1.2` open | no acceptance-scope artifact proving default-path governed intro before search output | test-layer gap |
| Task `4.3` open | no explicit planning-gate rerun artifact after implementation | authority revalidation gap |

### Design implication

The next remediation slice should be treated as **verification-completion design**, not as another runtime feature design.

That slice should add only the missing closure surfaces:
- one promoted-runtime behavioral proof for default-path governed intro/render after promotion,
- one explicit Strict-TDD evidence section in `apply-progress.md`,
- one explicit post-implementation planning-gate rerun artifact,
- and, if needed, one acceptance-level test artifact that proves the default-path contract at the intended layer.

### Non-goals for the remediation slice

The next slice should **not** redesign routing, banner presentation, or canonical artifact ownership again unless new evidence disproves the current implementation. Reopening the runtime design without new contrary evidence would be churn, not architecture.
