# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Malformed external frontmatter is auditable from the live manifest

The system MUST provide a deterministic audit surface that reads the live global `skills_manifest.json`, opens each referenced source `SKILL.md`, and reports malformed YAML frontmatter by file path, source root, and parser error family.

#### Scenario: audit reproduces the broken set from the live manifest
- GIVEN the live global manifest references malformed external skills
- WHEN the audit surface runs
- THEN it SHALL report each failing file path
- AND it SHALL classify each failure by parser error family

#### Scenario: audit remains manifest-backed
- GIVEN generated hub artifacts and external skills both exist
- WHEN malformed frontmatter is evaluated
- THEN the manifest-backed source paths SHALL be the enumerator of record
- AND ad hoc file discovery SHALL NOT redefine the broken set silently

### Requirement: Source-author repairs preserve authority boundaries

Malformed skill metadata MUST be repaired at the external source `SKILL.md` files themselves. Generated manifest or context-pack artifacts MUST NOT be hand-edited as a substitute for source-author fixes.

#### Scenario: source-author repair updates the broken file only
- GIVEN a malformed external `SKILL.md`
- WHEN the repair is applied
- THEN the source file SHALL become valid YAML
- AND generated hub artifacts SHALL remain untouched until normal rebuild/sync occurs

#### Scenario: generated artifacts are not patched directly
- GIVEN a malformed source file still exists
- WHEN an operator attempts to patch generated manifest state only
- THEN that action SHALL be treated as invalid for this change
- AND the source-author repair requirement SHALL remain open

### Requirement: Broken-set verification uses the same audit path before and after repair

The system MUST verify the repair by rerunning the same manifest-backed frontmatter audit used to discover the failures. Success SHALL mean zero failing entries in the previously tracked broken set.

#### Scenario: verify reaches zero after repair
- GIVEN all tracked malformed source files were repaired
- WHEN the same audit surface reruns
- THEN the broken set SHALL be zero
- AND no previously tracked file SHALL remain malformed

#### Scenario: one tracked file remains broken
- GIVEN any tracked malformed file still has invalid YAML frontmatter
- WHEN verification runs
- THEN the audit SHALL fail
- AND the change SHALL NOT be considered complete
