# Query Linter Integration Guide

## Overview

The Query Linter enhances `ctx search` by applying semantic classification and intelligent expansion to vague queries using anchor-based guidance.

## Processing Flow

```
Raw Query
    ↓
QueryNormalizer (lowercase, strip, collapse whitespace)
    ↓
QueryLinter (if enabled): classify + expand if vague
    ├─→ Classify: vague / semi / guided / disabled
    ├─→ Expand: add anchors from configs/anchors.yaml
    └─→ Return: expanded_query or original query
    ↓
QueryNormalizer.tokenize (tokenize FINAL query post-linter)
    ↓
QueryExpander (alias expansion via _ctx/aliases.yaml)
    ↓
ContextService (weighted search across all terms)
    ↓
Results
```

## Query Classification

| Class | Description | Expansion |
|-------|-------------|-----------|
| **vague** | < 3 tokens OR no anchors | YES - adds strong/weak anchors |
| **semi** | 3-4 tokens, some anchors | NO |
| **guided** | 5+ tokens, 1+ strong anchor | NO |
| **disabled** | Linter disabled or config missing | NO |

## Configuration

### 1. Create `configs/anchors.yaml`

```yaml
anchors:
  strong:
    files:
      - "agent.md"
      - "prime.md"
      - "skill.md"
  weak:
    files:
      - "config.md"
      - "setup.md"
```

### 2. (Optional) Create `configs/aliases.yaml`

```yaml
aliases:
  - source: "config"
    targets: ["configuration", "setup", "settings"]
```

## Usage

### Enable Linting (Environment Variable)

```bash
# Enable globally for all commands
export TRIFECTA_LINT=1
trifecta ctx search --segment . --query "config"
```

### Disable Linting (Flag)

```bash
# Explicitly disable for this search
trifecta ctx search --segment . --query "config" --no-lint
```

### Examples

#### Vague Query → Expansion
```bash
$ TRIFECTA_LINT=1 trifecta ctx search --segment . --query "config"
# Query classified as: vague
# Expanded to: "config agent.md prime.md"
# Results include hits for all expanded terms
```

#### Guided Query → No Expansion
```bash
$ TRIFECTA ctx search --segment . --query "agent.md template creation code file"
# Query classified as: guided (5+ tokens, 1 strong anchor)
# No expansion: query is already specific
```

#### Semi-Guided Query → No Expansion
```bash
$ TRIFECTA ctx search --segment . --query "config agent.md setup"
# Query classified as: semi (3 tokens, 1 anchor)
# No expansion: query has some structure
```

## Telemetry

### Metrics

- `ctx_search_linter_expansion_count`: Number of queries expanded
- `ctx_search_linter_class_{vague,semi,guided,disabled}_count`: Per-class counts

### Event Data

Each `ctx.search` event includes:
```json
{
  "linter_query_class": "vague",
  "linter_expanded": true,
  "linter_added_strong_count": 2,
  "linter_added_weak_count": 0,
  "linter_reasons": ["Query has < 3 tokens", "No strong anchors detected"]
}
```

## Troubleshooting

### Linter Not Expanding Queries

1. **Check if enabled**:
   ```bash
   echo $TRIFECTA_LINT  # Should be "1" or "true"
   ```

2. **Check config exists**:
   ```bash
   ls configs/anchors.yaml  # Should exist
   ```

3. **Check for warnings**:
   ```bash
   trifecta ctx search --segment . --query "config" 2>&1 | grep ConfigLoader
   ```

### Query Not Being Expanded

1. **Check query class**: Vague queries expand; semi/guided do not
2. **Add anchors to configs/anchors.yaml**: Strong anchors trigger expansion
3. **Verify query length**: < 3 tokens = vague, 3-4 = semi, 5+ = guided

## Testing

```bash
# Run unit tests
uv run pytest tests/unit/test_search_usecase_linter.py -v

# Run integration tests
uv run pytest tests/integration/test_ctx_search_linter.py -v

# Run all linter tests
uv run pytest -k "linter" -v
```

## Architecture

### Two-Stage Expansion

1. **Query Linter (Semantic Layer)**: Anchor-based expansion for vague queries
2. **Query Expander (Syntactic Layer)**: Alias-based expansion for all queries

This separation allows:
- Semantic understanding via anchors (strong/weak file guidance)
- Synonym support via aliases (Spanish/English terms)
- Conservative rollout via feature flag
- Graceful degradation when configs missing

## Future Enhancements

- [ ] Add fuzzy matching for anchor suggestions
- [ ] Support custom anchor weights per project
- [ ] Add query reformulation feedback loop
- [ ] Enable by default after testing period
