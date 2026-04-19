# Delta for Skill Hub Authority

## ADDED Requirements

### Requirement: YAML Frontmatter Block Scalar Parsing

The manifest builder `parse_frontmatter()` **MUST** correctly extract the `description` value from all valid YAML frontmatter shapes: folded block scalars (`>`, `>+`, `>-`), literal block scalars (`|`, `|+`, `|-`), double-quoted strings, single-quoted strings, and plain (unquoted) strings.

When a block scalar indicator is detected, the parser **MUST** collect all indented continuation lines following the indicator and join them with spaces (folded) or newlines (literal). The parser **SHALL** return `None` for malformed frontmatter and **MUST NOT** store the raw indicator character (e.g. `>`) as the description value.

#### Scenario: YAML folded block scalar (`>`)

- GIVEN a SKILL.md with frontmatter `description: >` followed by indented lines `Use when X.\n  Also Y.`
- WHEN `parse_frontmatter()` extracts the description
- THEN the returned description **SHALL** be `"Use when X. Also Y."`
- AND the manifest entry **MUST NOT** contain `"description": ">"`

#### Scenario: YAML literal block scalar (`|`)

- GIVEN a SKILL.md with frontmatter `description: |` followed by indented lines
- WHEN `parse_frontmatter()` extracts the description
- THEN the returned description **SHALL** preserve line breaks between continuation lines

#### Scenario: Double-quoted string (existing behavior preserved)

- GIVEN a SKILL.md with frontmatter `description: "Use when building dashboards"`
- WHEN `parse_frontmatter()` extracts the description
- THEN the returned description **SHALL** be `"Use when building dashboards"` (quotes stripped)

#### Scenario: Plain unquoted string

- GIVEN a SKILL.md with frontmatter `description: Use when debugging`
- WHEN `parse_frontmatter()` extracts the description
- THEN the returned description **SHALL** be `"Use when debugging"`

#### Scenario: Empty or missing description

- GIVEN a SKILL.md with frontmatter `description: >` and no continuation lines, or missing `description` key
- WHEN `parse_frontmatter()` processes it
- THEN the function **SHALL** return an empty string or `None` respectively
- AND the skill **MUST NOT** appear in the manifest with a raw indicator as description

### Requirement: Manifest Description Integrity

After manifest regeneration via `audit_skill_hub.py --write-manifest`, the generated `skills_manifest.json` **MUST NOT** contain any skill entry where the `description` value is a raw YAML block indicator (`>`, `|`, `>+`, `|-`, etc.) or is empty/under 3 characters when the source SKILL.md has a valid description.

#### Scenario: No raw indicators in regenerated manifest

- GIVEN 467 registered skills with valid SKILL.md frontmatter across all sources
- WHEN `audit_skill_hub.py --write-manifest` regenerates the manifest
- THEN zero entries **SHALL** have `description` equal to `">"`, `"|"`, or any other raw indicator
- AND the count of entries with `description` length ≤ 2 **SHALL** be zero

#### Scenario: Card promotion returns all matching skills

- GIVEN the regenerated manifest with correct descriptions
- WHEN `skill-hub --cards "sdd gate"` is executed
- THEN all skills whose description matches "sdd" or "gate" **SHALL** be promoted
- AND the result count **SHALL** match the search hit count for the same query

## REMOVED Requirements

None.

## Acceptance Criteria

1. `audit_skill_hub.py --write-manifest` produces a manifest with **zero** entries where `description` is a raw YAML indicator character.
2. `skill-hub --cards "sdd gate"` returns ALL SDD-related skills (not just 1).
3. `skill-hub --cards "sdd"` promotes all skills containing "sdd" in name or description.
4. Previously-working quoted-string skills (pi-agent-skills source) continue parsing correctly — zero regressions.

## Out of Scope

- Refactoring shared YAML parsing into a common module.
- Normalizing SKILL.md files (source files are valid YAML; the parser is the bug).
- Adding fallback description extraction in card promotion code.
