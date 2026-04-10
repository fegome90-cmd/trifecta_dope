## Exploration: skill-hub authority reanchor

### Current State
`skill-hub` has split authority: policy and canonical builder live in Trifecta, the live manifest writer lives in an external local toolchain, the runtime reads only `_ctx/context_pack.json`, and the live pack is generic-shaped rather than `skill_hub`-shaped. The official `SkillHubIndexingStrategy` fails closed on the current live manifest/root mismatch, so the runtime corpus does not belong cleanly to the branch declared by the code.

### Affected Areas
- `src/domain/segment_indexing_policy.py` — policy detection still permits generic fallback.
- `src/application/use_cases.py` — separates the generic writer from the `skill_hub` writer.
- `src/application/skill_hub_indexing_strategy.py` — declares the intended manifest-driven contract.
- `src/domain/skill_manifest.py` — migrates v1 input and exposes canonical path mismatches.
- `src/application/context_service.py` — runtime trusts the persisted pack only.
- `src/infrastructure/aliases_fs.py` / `src/infrastructure/cli_skills.py` — downstream still read old manifest shape.
- `scripts/ingest_trifecta.py` — legacy direct pack writer that can contaminate runtime state.

### Approaches
1. **Guardrail-only containment**
   - Pros: low blast radius, quick protection.
   - Cons: split authority survives.
   - Effort: Medium

2. **Full re-anchor inside Trifecta**
   - Pros: clean SSOT, one writer per surface.
   - Cons: highest migration cost.
   - Effort: High

3. **Canonical admission boundary with later hard cut**
   - Pros: closes authority first, removes external ownership later.
   - Cons: needs disciplined cutover plan.
   - Effort: Medium/High

### Recommendation
Use **approach 3 as the transition** and **approach 2 as the end state**: external inputs may remain only as staging, but canonical manifest, canonical pack, and provenance seal must move under Trifecta ownership immediately.

### Risks
- Current live runtime may become inadmissible on purpose.
- Naming normalization must be made singular (`playwright-cli` vs `playwright`).
- Consumers that still expect old manifest shape must be cut over without dual runtime contracts.

### Ready for Proposal
Yes — create a strict proposal that defines authority surfaces, one writer per surface, admission receipts, and a no-generic-fallback rule for `skill_hub`.
