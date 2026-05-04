# Design: repair global skill frontmatter

## Technical Approach
Keep the authority chain boring and strict: source `SKILL.md` files are the only place where malformed metadata should be repaired; generated hub artifacts remain downstream outputs. The repo gains a deterministic audit surface that reads the live manifest, parses frontmatter exactly once per referenced source, and reports failures by source root and YAML error class.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Authority for repair | Fix external source `SKILL.md` files directly | Patch `skills_manifest.json` or `context_pack.json` by hand | Generated artifacts are evidence/output, not source authority. |
| Audit ownership | Repo-owned script/test reads live manifest and parses frontmatter | Ad hoc shell one-liners only | A durable audit is how you stop this from regressing again, loco. |
| Fix style | Minimal syntax-preserving edits (quotes, escaping, valid lists/maps) | Content rewrites or aggressive normalization | We need valid YAML, not a semantic rewrite project. |
| Apply strategy | Two phases: repo diagnostics first, external source edits second | Mix repo and external edits blindly | Keeps the blocked permission boundary explicit and auditable. |
| Verification source | Recompute broken set from the same manifest-backed scan | Infer success from `skill-hub` search output only | Search can hide corruption; parser-level proof is stricter. |

## Data Flow

```text
live manifest
  -> repo audit helper/test
     -> open each source_path
     -> parse YAML frontmatter
     -> classify failures by file + error type
source-author fix
  -> rerun audit helper/test
  -> zero broken entries expected
  -> optional hub rebuild/regeneration
```

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/repair-global-skill-frontmatter/proposal.md` | Create | Scope and rollback plan. |
| `openspec/changes/repair-global-skill-frontmatter/design.md` | Create | Authority and implementation design. |
| `openspec/changes/repair-global-skill-frontmatter/tasks.md` | Create | Task breakdown with blocked external apply step. |
| `openspec/changes/repair-global-skill-frontmatter/specs/skill-hub-authority/spec.md` | Create | Contract delta for malformed external frontmatter auditing and repair. |
| Repo audit/test files | Future modify | Deterministic audit for live-manifest frontmatter validity. |
| External broken `SKILL.md` files | Future modify | Syntax-only frontmatter repairs. |

## Interfaces / Contracts
- The live manifest remains the enumerator of the broken set for this change.
- The audit surface MUST report file path, source root, and YAML error class for each failing entry.
- External skill fixes MUST preserve the intended metadata fields while making the YAML syntactically valid.
- Generated hub artifacts MUST only change through normal rebuild/sync flow after source fixes.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Frontmatter parser audit classification and stable reporting | pytest over audit helper with malformed fixtures mirroring current failures. |
| Integration | Live-manifest scan reproduces the current broken set deterministically | repo test or script reading the manifest and source files. |
| Verification | Broken set reaches zero after source fixes | rerun the same scan; no alternate success metric. |

## Migration / Rollout
1. Land repo-owned diagnostics first.
2. Obtain approval to edit external skill files.
3. Fix the 14 files in small batches by error family.
4. Re-run audit and only then rebuild/regenerate the hub state if needed.

## Open Questions
- Hybrid persistence requested by user cannot be fully honored here because Engram tools are unavailable in this runtime; filesystem/OpenSpec artifacts are the authoritative record for this run.
