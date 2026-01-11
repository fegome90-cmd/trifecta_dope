# Agent Prompt: WO-0010 Field Exercises v1

## Context
You are executing WO-0010 to establish a quantitative benchmark for the Trifecta search system using real-world queries.

## Objective
Create a reproducible Field Exercises evaluation:
1. **Dataset**: 20 real queries (varied difficulty and type)
2. **A/B Test**: Run queries with linter OFF vs ON
3. **Report**: Generate metrics (zero-hit rate, avg hits, delta)
4. **Gate**: Verify zero_hit_rate_on < 30%

## Tasks (Execute in Order)

### TASK 1: Create Dataset (eval/field_exercises_v1.yaml)
```yaml
version: 1
description: "Real-world queries for search quality evaluation"
queries:
  - id: FE-001
    type: technical  # technical | conceptual | discovery
    query: "How does the LSP daemon handle concurrent requests?"
    expected_min_hits: 2  # Minimum hits to consider non-zero
    rationale: "Tests technical documentation discovery"
  
  # ... (add 19 more varied queries)
```

**Query Mix**:
- 6 technical (specific implementation details)
- 6 conceptual (how things work, architecture)
- 8 discovery (vague, exploratory)

**Selection Criteria**:
- Use real questions you would ask about this codebase
- Ensure queries CAN match existing content (docs/, src/, README)
- Vary complexity: easy (1-2 word), medium (phrase), hard (multi-concept)

### TASK 2: Create Runner (eval/scripts/run_field_exercises_ab.py)
```python
#!/usr/bin/env python3
"""
Field Exercises A/B Evaluation Runner

Usage:
  --validate: Check dataset schema
  --mode off: Run queries with --no-lint
  --mode on: Run queries with TRIFECTA_LINT=1
  --output FILE: Save results log
"""

import subprocess
import yaml
from pathlib import Path

def load_dataset(path: Path):
    # Load field_exercises_v1.yaml
    pass

def run_query_cli(query: str, mode: str, segment: Path):
    # Execute: uv run trifecta ctx search --segment . --query "..." --limit 10
    # If mode == "off": add --no-lint
    # If mode == "on": set TRIFECTA_LINT=1
    pass

def calculate_metrics(results):
    # zero_hit_rate = (queries with 0 hits) / total_queries
    # avg_hits = sum(hits) / total_queries
    # delta = avg_hits_on - avg_hits_off
    pass

def generate_report(results_off, results_on, output_path):
    # Write docs/reports/field_exercises_v1_results.md
    pass
```

**Key Requirements**:
- Use `uv run trifecta ctx search --segment . --query "..." --limit 10`
- Parse output to count hits (look for "Found X chunks" or parse JSON if available)
- Log full CLI output to _ctx/logs/field_ex_{off,on}.log
- Return structured results for metrics calculation

### TASK 3: Run Evaluation
```bash
# Validate dataset
uv run python eval/scripts/run_field_exercises_ab.py --validate

# Run OFF mode
uv run python eval/scripts/run_field_exercises_ab.py --mode off --output _ctx/logs/field_ex_off.log

# Run ON mode  
uv run python eval/scripts/run_field_exercises_ab.py --mode on --output _ctx/logs/field_ex_on.log

# Generate report
uv run python eval/scripts/run_field_exercises_ab.py --generate-report
```

### TASK 4: Generate Report (docs/reports/field_exercises_v1_results.md)
```markdown
# Field Exercises v1 - Evaluation Results

**Date**: 2026-01-06
**Dataset**: 20 real-world queries
**Modes**: OFF (no linter) vs ON (linter enabled)

## Metrics

| Metric | OFF | ON | Delta |
|--------|-----|----|----- |
| Zero-hit rate | X% | Y% | ΔZ% |
| Avg hits per query | N | M | ΔK |
| Queries with 0 hits | J | K | ΔL |

## Gate Status

**Zero-hit rate ON**: Y%  
**Threshold**: < 30%  
**Status**: ✅ PASS | ❌ FAIL

## Query Breakdown

### Queries with 0 hits (ON mode)
- FE-XXX: "query text" (reason: ...)

### Top performers
- FE-XXX: "query text" (10 hits)

## Recommendations
...
```

### TASK 5: Update Session
```bash
printf '\n## 2026-01-06 XX:XX UTC - Field Exercises v1 Evaluation\n- **WO**: WO-0010\n- **Dataset**: 20 real queries (6 technical, 6 conceptual, 8 discovery)\n- **Results**: zero_hit_rate_on=Y%, avg_hits_on=M\n- **Gate**: Y% < 30% → PASS/FAIL\n- **Commit**: feat(eval): add Field Exercises v1 benchmark\n' >> _ctx/session_trifecta_dope.md
```

### TASK 6: Commit
```bash
git add eval/ docs/reports/field_exercises_v1_results.md _ctx/logs/field_ex_*.log _ctx/session_trifecta_dope.md
git commit -m "feat(eval): add Field Exercises v1 benchmark

Created quantitative benchmark for search quality:
- Dataset: 20 real-world queries (field_exercises_v1.yaml)
- A/B: OFF vs ON linter evaluation
- Metrics: zero_hit_rate, avg_hits, delta
- Gate: zero_hit_rate_on < 30%

Results:
- Zero-hit rate ON: Y%
- Avg hits ON: M
- Gate: PASS/FAIL

Evidence:
- _ctx/logs/field_ex_off.log
- _ctx/logs/field_ex_on.log
- docs/reports/field_exercises_v1_results.md"
```

## Rules (MANDATORY)

1. **CLI Only**: Use `uv run trifecta ctx search` for all queries
2. **Session Log**: Update `_ctx/session_trifecta_dope.md` with summary
3. **No --no-verify**: Pre-commit hooks must run
4. **Evidence**: Commit logs to `_ctx/logs/`
5. **Dataset Quality**: Queries must be realistic (not synthetic edge cases)

## Success Criteria

- ✅ Dataset has 20 queries with expected_min_hits
- ✅ Runner executes both OFF and ON modes
- ✅ Report has zero_hit_rate, avg_hits, delta
- ✅ Gate verified: zero_hit_rate_on < 30%
- ✅ Logs committed to _ctx/logs/
- ✅ Session updated
- ✅ Commit without --no-verify

## Output

Final message should include:
```
WO-0010 Field Exercises v1 COMPLETE

Dataset: 20 queries
Results:
  - Zero-hit rate OFF: X%
  - Zero-hit rate ON: Y%
  - Avg hits ON: M
  - Delta ON-OFF: +K hits

Gate: zero_hit_rate_on < 30% → PASS/FAIL

Commit: SHA
Files: eval/, docs/reports/, _ctx/logs/
```
