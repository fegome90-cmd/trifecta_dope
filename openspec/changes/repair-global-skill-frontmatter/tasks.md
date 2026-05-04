# Tasks: repair global skill frontmatter

## Phase 1: Explore / freeze the broken set

- [x] 1.1 Confirm the live broken set from `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json` and record the 14 failing files.
- [x] 1.2 Classify the failures by YAML error family (`ScannerError` vs `ParserError`) and by source root.
- [x] 1.3 Reconcile the observed `14 total` vs `12 fuera de scope` diagnosis and record the likely in-scope/out-of-scope partition.

## Phase 2: Red — repo-owned diagnostics

- [x] 2.1 Add a repo-owned audit helper or test fixture that reads the live manifest and reports malformed frontmatter deterministically.
- [x] 2.2 Add focused tests mirroring both current error families so future malformed skills fail with stable diagnostics.
- [x] 2.3 Prove the diagnostic surface fails when any tracked broken file remains malformed.

## Phase 3: Green — external source-author repairs

- [x] 3.1 Repair the 11 `ScannerError` files using minimal quoting/description fixes.
- [x] 3.2 Repair the 3 `ParserError` files using minimal escaping/list-structure fixes.
- [x] 3.3 Re-run the audit after each batch to avoid hiding new breakage behind aggregate counts.
- [x] 3.4 Regenerate hub derived artifacts through the normal rebuild/sync flow only after source files are fixed.

## Phase 4: Verify / closeout

- [x] 4.1 Run the manifest-backed audit and confirm the broken set is zero.
- [x] 4.2 Capture exact files changed, permission boundary decisions, and residual warnings in `apply-progress.md`.
- [x] 4.3 Produce `verify-report.md` with before/after counts and error families.
- [x] 4.4 Archive the change only after repo diagnostics and external source fixes are both complete.

## Current Blocking Condition

- External source edits are blocked until permission is granted to modify files under:
  - `~/.claude/skills`
  - `~/.pi/agent/skills`
  - `~/Developer/examen_grado/skills`
