# Tasks: Fix skill-hub --cards YAML Folded Block Parsing

## Phase 1: Source Analysis

- [ ] 1.1 Read `register_skill.py` lines 84-130 — extract `_parse_yaml_value()` signature, `_BLOCK_INDICATORS` frozenset, and all three branches (quoted, block scalar, plain)
- [ ] 1.2 Read `audit_skill_hub.py` line ~77 — locate current `parse_frontmatter()` and its naive `re.search(r"^description:\s*(.+)$", ...)` regex
- [ ] 1.3 Confirm the two files share no import path — verify code-port is the only viable approach (design decision A)

## Phase 2: Implementation

- [ ] 2.1 Add `import sys` to top of `audit_skill_hub.py` (needed for `sys.stderr` warnings in error branch)
- [ ] 2.2 Add `_BLOCK_INDICATORS = frozenset({">", ">+", ">-", "|", "|+", "|-"})` constant before `parse_frontmatter()`
- [ ] 2.3 Add `_parse_yaml_value(block_text: str, key: str) -> str | None` function (~47 lines, ported from `register_skill.py`) — handles quoted strings, block scalars with indented continuation lines, and plain strings
- [ ] 2.4 Rewrite `parse_frontmatter()` body: replace naive regex with `_parse_yaml_value(block, "name")` and `_parse_yaml_value(block, "description")` calls

## Phase 3: Verification

- [ ] 3.1 Run `python audit_skill_hub.py --report-out /tmp/after.json` — confirm `suspect_descriptions` count drops from ~35 to 0 (spec: "zero entries with raw indicator")
- [ ] 3.2 Run `python audit_skill_hub.py --write-manifest` — regenerate manifest, grep for `"description": ">"` returns zero matches
- [ ] 3.3 Run `skill-hub --cards "sdd gate"` — confirm all SDD skills appear, not just 1 (spec scenario: card promotion)
- [ ] 3.4 Run `skill-hub --cards "security"` — spot-check quoted-string skills still parse correctly, zero regressions (spec: existing behavior preserved)
