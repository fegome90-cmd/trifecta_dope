# Proposal: Skill-hub Authority Anchor

## Intent

Reorder `skill-hub` around one authority per surface so runtime state is produced, admitted, and consumed under a single Trifecta-owned contract. This removes split ownership between external manifest writers, generic/legacy pack writers, and downstream consumers.

## Scope

### In Scope
- Define authority surfaces for upstream input, canonical manifest, runtime pack, admission receipt, runtime load, and aliases/CLI.
- Establish a canonical `skill_hub` admission path with no generic fallback.
- Migrate downstream consumers to the canonical manifest contract.

### Out of Scope
- Reindexing or repairing the current live `skills-hub` segment.
- Redesigning generic segment indexing.
- Manual state surgery on runtime artifacts.

## Capabilities

### New Capabilities
- `skill-hub-authority`: Single-authority governance for manifest admission, pack production, provenance sealing, and downstream contract consumption.

### Modified Capabilities
- None

## Approach

Create one canonical admission boundary inside Trifecta: compatibility input may enter there, but only the normalized manifest and the `skill_hub` pack produced from it are authoritative. Runtime consumers and alias consumers read only admitted artifacts.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/segment_indexing_policy.py` | Modified | Remove `skill_hub` downgrade semantics. |
| `src/domain/skill_manifest.py` | Modified | Define canonical persisted contract and normalization boundary. |
| `src/application/use_cases.py` | Modified | Make `skill_hub` pack promotion governed and exclusive. |
| `src/application/context_service.py` | Modified | Require admitted pack for runtime load. |
| `src/infrastructure/aliases_fs.py` | Modified | Cut over to canonical manifest only. |
| `src/infrastructure/cli_skills.py` | Modified | Consume canonical manifest-derived aliases only. |
| `scripts/ingest_trifecta.py` | Modified/Deprecated | Invalid for `skill_hub` runtime output. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Current live runtime becomes invalid | High | Fail closed and keep rollback on last admitted pair. |
| Consumer drift during cutover | Medium | Contract tests on canonical fixtures only. |
| Hidden manual workflows survive | Medium | Explicitly deprecate non-Trifecta writers in docs and receipts. |

## Rollback Plan

Rollback only to the last Trifecta-admitted manifest+pack pair. Revert Trifecta governance code if needed, but do not reopen authority to external or legacy runtime writers.

## Dependencies

- Clear canonical naming rule for source-to-relative-path normalization.
- Receipt format that binds manifest fingerprint to pack fingerprint.

## Success Criteria

- [ ] `skill_hub` never falls back to `generic`.
- [ ] Runtime accepts only admitted `skill_hub` packs.
- [ ] Downstream consumers read only the canonical manifest contract.
