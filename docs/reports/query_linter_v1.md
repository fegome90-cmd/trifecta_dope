# Query Linter v1 (Phase 3)

**Component**: `src/domain/query_linter.py`
**Status**: Verified (PASS)

## Classification Rules

The linter deterministically assigns a class based on token count and anchor density.

*   **GUIDED**: `tokens >= 5` AND (`strong >= 1` OR `total_anchors >= 2`)
    *   *Intent*: User knows what they want and provides context.
*   **VAGUE**: `tokens < 3` OR `total_anchors == 0`
    *   *Intent*: User is lost or lazy. Needs help (expansion).
*   **SEMI**: Everything else.
    *   *Intent*: Ambiguous.

## Expansion Rules (Deterministic)

Applied **ONLY** to `VAGUE` queries.

1.  **Doc Boost**: If query contains intent terms (`docs`, `guía`, `manual`), add `docs/` and `readme.md` (strong anchors).
2.  **Default Boost**: If query is very short (<= 2 tokens) and no doc intent, add `agent.md` and `prime.md` as entrypoints.
3.  **Limits**: Max 2 added strong anchors. No duplicates.

## Examples (Input -> Plan)

### 1. Vague Default
**Query**: "config"
**Plan**:
```json
{
  "query_class": "vague",
  "changed": true,
  "expanded_query": "config agent.md prime.md",
  "changes": {
    "added_strong": ["agent.md", "prime.md"],
    "reasons": ["vague_default_boost"]
  }
}
```

### 2. Vague Doc Intent
**Query**: "docs"
**Plan**:
```json
{
  "query_class": "vague",
  "changed": true,
  "expanded_query": "docs docs/ readme.md",
  "changes": {
    "added_strong": ["docs/", "readme.md"],
    "reasons": ["doc_intent_boost"]
  }
}
```

### 3. Guided (English)
**Query**: "check agent.md template creation code"
**Plan**:
```json
{
  "query_class": "guided",
  "changed": false,
  "expanded_query": "check agent.md template creation code",
  "changes": {}
}
```

### 4. Spanish Alias (Guided/Semi)
**Query**: "Muéstrame documentación sobre la persistencia de sesión"
**Plan**:
```json
{
  "query_class": "guided",
  "changed": false,
  "anchors_detected": {
    "aliases_matched": ["persistencia de sesión"],
    "strong": ["session.md", "session append"]
  }
}
```

### 5. Semi (No expansion)
**Query**: "update telemetry logic"
**Plan**:
```json
{
  "query_class": "semi",
  "changed": false,
  "anchors_detected": {
    "strong": ["telemetry"],
    "weak": []
  }
}
```

## Out of Scope
*   **Retries**: No retry logic here. The expanded query is just a suggestion for the next layer.

## CLI Integration (Phase 4)

**Status**: ✅ INTEGRATED (2026-01-05)

### Integration Point
- **File**: `src/application/search_get_usecases.py:52-73`
- **Location**: Between QueryNormalizer and QueryExpander
- **Trigger**: Conditional via `enable_lint` parameter (default: False)

### CLI Flags
- `--no-lint`: Disable query linting for this search (default: present = disabled)
- `TRIFECTA_LINT`: Environment variable to enable/disable globally
  - `TRIFECTA_LINT=1` or `true`: Enable linting
  - `TRIFECTA_LINT=0` or `false`: Disable linting
  - Default (unset): DISABLED (conservative rollout)

### Examples

#### Vague Query (With Expansion)
```bash
$ TRIFECTA_LINT=1 trifecta ctx search --segment . --query "config"
# Internally expanded to: "config agent.md prime.md"
```

#### Guided Query (No Expansion)
```bash
$ TRIFECTA ctx search --segment . --query "agent.md template creation"
# No expansion: query already guided
```

#### Disable Linting
```bash
$ trifecta ctx search --segment . --query "config" --no-lint
# Linter explicitly disabled via flag
```

### Test Coverage
- Unit tests: 3 tests in `tests/unit/test_search_usecase_linter.py`
- Integration tests: 5 tests in `tests/integration/test_ctx_search_linter.py`
- All tests passing (8/8)

### Telemetry
Metrics tracked:
- `ctx_search_linter_expansion_count`: Number of queries expanded
- `ctx_search_linter_class_{vague,semi,guided,disabled}_count`: Classification counts
- Event `ctx.search` includes linter metadata (query_class, linter_expanded, added_strong/weak_count, reasons)
