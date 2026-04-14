# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Governed cards wrapper entrypoint
The public `skill-hub` wrapper MUST accept `--cards` and `--limit`, and when cards mode is requested it MUST delegate to the governed adjacent helper while preserving helper stdout, stderr, and exit semantics.

#### Scenario: renderable cards result
- GIVEN `skill-hub --cards "query" --limit 1`
- WHEN the governed helper returns a renderable result
- THEN the wrapper SHALL exit `0`
- AND it SHALL stream the helper stdout unchanged.

#### Scenario: non-renderable cards result
- GIVEN `skill-hub --cards "query" --limit 1`
- WHEN the governed helper returns a non-renderable outcome
- THEN the wrapper SHALL preserve the helper stderr and non-zero exit code unchanged.

### Requirement: Governed card classification fails closed
The governed cards runtime MUST only promote trusted `skill` or confidently-normalized `repo` hits into cards, and MUST classify metadata-only or unsupported hits as non-renderable without claiming success.

#### Scenario: metadata-only search hits
- GIVEN search results containing only `prime`, `session`, or `agent` metadata hits
- WHEN the governed cards runtime builds a render plan
- THEN it SHALL return a non-renderable outcome
- AND it SHALL explain that the results are administrative metadata rather than executable skills.

#### Scenario: insufficient repo confidence
- GIVEN a `repo:*` hit without a trusted read path or skill fields
- WHEN the governed cards runtime classifies the result
- THEN it SHALL fail closed as unsupported
- AND it SHALL not emit a skill card.

### Requirement: Deprecated Python entry remains a shim only
The legacy `scripts/skill_hub_cards.py` entrypoint MUST remain a thin delegator to the governed helper and MUST NOT reintroduce independent parsing, normalization, or rendering logic.

#### Scenario: shim inspection
- GIVEN the deprecated Python entrypoint
- WHEN it is inspected or executed
- THEN it SHALL delegate to `skill-hub-cards`
- AND all cards logic SHALL live outside the shim.
