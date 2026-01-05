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
*   **CLI Integration**: This logic is pure domain. Not yet hooked into `ctx search`.
*   **Retries**: No retry logic here. The expanded query is just a suggestion for the next layer.
