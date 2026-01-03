# Error→Prompt System

## Overview

The Error→Prompt system generates actionable recovery prompts when CLI commands fail, making it easier for agents to self-correct without manual intervention.

## Error Prompt Format

When a command fails (`returncode != 0`), the harness generates an Error Prompt Card:

```
❌ Command Failed: <command>

Exit Code: <int>
Error Class: <class>
Error Code: <code>

Cause:
<detailed cause from Error Card>

Recovery Steps:
1. <deterministic step 1>
2. <deterministic step 2>
3. <deterministic step 3>
```

## Example Error Prompts

### SEGMENT_NOT_INITIALIZED

```
❌ Command Failed: uv run trifecta ctx sync -s /tmp/test

Exit Code: 1
Error Class: Precondition
Error Code: SEGMENT_NOT_INITIALIZED

Cause:
Segment directory exists but is not initialized.
Missing: _ctx/trifecta_config.json

Recovery Steps:
1. Run: trifecta create -s <segment_path>
2. Verify prime file was created: ls _ctx/prime_*.md
3. Run: trifecta ctx sync -s <segment_path>
```

### PRIME_FILE_NOT_FOUND

```
❌ Command Failed: uv run trifecta ctx get -s . --ids prime:abc

Exit Code: 1
Error Class: Runtime
Error Code: PRIME_FILE_NOT_FOUND

Cause:
Expected prime file not found: _ctx/prime_<segment>.md

Recovery Steps:
1. Check segment directory structure
2. Run: trifecta refresh-prime -s <segment_path>
3. Verify _ctx/prime_*.md exists
```

## Harness Usage

### Python Harness (v1.1)

**v1.1 Features**:
- ✅ Real ID resolution from `context_pack.json`
- ✅ Typed numeric fields in PD_REPORT (int, not str)
- ✅ Deterministic fallback (pack → sync → error)

```bash
# Run harness on current segment
python scripts/harness_blackbox.py .

# Example output:
✅ Resolved IDs: ['skill:03ba77a5e8', 'prime:363a719791']
▶️  Running: uv run trifecta ctx get -s . --ids skill:03ba77a5e8,prime:363a719791 --pd-report
   ✅ Success
   📊 PD_REPORT: {'chunks_returned': 2, 'strong_hit': 0}  # Note: int, not str

# Output: _ctx/telemetry/harness_results.jsonl
```

**Note**: IDs are automatically resolved - no more hardcoded "prime:abc"!

### Programmatic Usage

```python
from scripts.harness_blackbox import run_command_with_extraction

result = run_command_with_extraction(
    ["uv", "run", "trifecta", "ctx", "get", "-s", ".", "--ids", "prime:abc", "--pd-report"]
)

if not result["success"]:
    if "error_prompt" in result:
        print(result["error_prompt"])  # Show recovery steps
```

## Error Card Extraction

The harness automatically extracts Error Cards from stderr by looking for:

1. **Error Code**: `TRIFECTA_ERROR_CODE: <code>`
2. **Class**: `CLASS: <class>`
3. **Cause**: Text between `CAUSE:` and `NEXT STEPS:`

## Recovery Step Patterns

### Deterministic (No LLM needed)

Recovery steps are **deterministic** based on error code:

| Error Code | Pattern |
|------------|---------|
| `SEGMENT_NOT_INITIALIZED` | create → verify → sync |
| `PRIME_FILE_NOT_FOUND` | check structure → refresh-prime → verify |
| Generic | check syntax → verify init → review cause |

## Integration with Agents

Agents can use Error Prompts to:

1. **Parse** the error from JSONL or stderr
2. **Extract** recovery steps (lines starting with numbers)
3. **Execute** steps sequentially
4. **Validate** success after each step

## Output Format (JSONL)

Each command run produces a JSON entry with **typed fields** (v1.1+):

```json
{
  "timestamp": "2026-01-02T11:45:00Z",
  "command": "uv run trifecta ctx get -s . --ids prime:abc,skill:xyz --pd-report",
  "returncode": 0,
  "success": true,
  "pd_report": {
    "v": "1",
    "stop_reason": "complete",
    "chunks_returned": 1,
    "chunks_requested": 1,
    "chars_returned_total": 512,
    "strong_hit": 0,
    "support": 0
  }
}
```

**Note**: Numeric fields (`chunks_returned`, `chunks_requested`, `chars_returned_total`, `strong_hit`, `support`) are **int**, not strings.

Or on failure:

```json
{
  "timestamp": "2026-01-02T11:45:00Z",
  "command": "uv run trifecta ctx sync -s /tmp/uninit",
  "returncode": 1,
  "success": false,
  "error_card": {
    "code": "SEGMENT_NOT_INITIALIZED",
    "class": "Precondition",
    "cause": "Missing _ctx/trifecta_config.json"
  },
  "error_prompt": "❌ Command Failed: ...\n\nRecovery Steps:\n1. ..."
}
```

## See Also

- [Error Cards](../src/cli/error_cards.py)
- [PD_REPORT Contract](PD_REPORT_CONTRACT.md)
- [Existing Harness](../scripts/agent_harness_fp.sh)
