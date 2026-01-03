# PD_REPORT Contract

## Overview

The `--pd-report` flag on `trifecta ctx get` emits a parseable metrics line for testing and automation.

## Format

```
PD_REPORT v=<int> <key>=<value> <key>=<value> ...
```

**Example**:
```
PD_REPORT v=1 stop_reason=evidence chunks_returned=1 chunks_requested=2 chars_returned_total=512 strong_hit=1 support=1
```

## Output Guarantees

1. **Single Line**: When `--pd-report` is set, Trifecta prints **exactly ONE** PD_REPORT line
2. **Last Line**: The PD_REPORT line **MUST be the last line** of stdout
3. **To stdout**: PD_REPORT is always written to stdout (not stderr)

## Parsing Rules

1. **Order-Independent**: Key order is **NOT guaranteed**. Parsers **MUST** be order-insensitive
2. **Ignore Unknown Keys**: Parsers **MUST** ignore unknown keys for forward compatibility
3. **Key-Value Format**: Each pair is `<key>=<value>` separated by spaces
4. **No Escaping**: Values do not contain spaces or special characters (design constraint)

## Invariant Keys (v=1)

Every PD_REPORT line **always** includes these 7 key-value pairs:

| Key | Type | Description |
|-----|------|-------------|
| `v` | int | Contract version (currently `1`) |
| `stop_reason` | string | Why retrieval stopped: `complete`, `budget`, `max_chunks`, `evidence`, `error` |
| `chunks_returned` | int | Number of chunks actually returned |
| `chunks_requested` | int | Number of chunks requested |
| `chars_returned_total` | int | Total characters returned across all chunks |
| `strong_hit` | 0\|1 | Evidence detection: query matches chunk title/ID (word boundary) AND chunk kind is `prime` |
| `support` | 0\|1 | Evidence detection: chunk text contains strict code definition patterns (`def <query>(`, `class <query>:`, etc.) with guards to avoid false positives |

### Semantic Definitions

**`strong_hit`**: Observable behavior
- Query token appears in chunk title or ID with word-boundary matching
- AND chunk kind (from ID prefix) is `prime:`
- Purpose: Identifies high-signal chunks

**`support`**: Observable behavior
- Chunk text contains strict patterns matching code definitions
- Patterns include: `def <query>(`, `class <query>:`, `class <query>(`
- Guards: Filters out keywords, comments, and partial matches
- Purpose: Confirms query represents an actual code symbol

## Evolution Rules

### Within v=1
- **Additive Only**: New keys may be **appended** at the end
- **Never Remove**: Existing keys cannot be removed
- **Never Rename**: Existing keys cannot be renamed
- **Never Change Semantics**: Existing key meanings are **stable**

### Breaking Changes
- Require incrementing to `v=2`
- Examples: removing keys, changing value types, changing semantics

## Example Usage

### Basic
```bash
$ uv run trifect ctx get -s . --ids prime:abc123,skill:xyz456 --mode excerpt --pd-report

Retrieved 2 chunk(s) (mode=excerpt, tokens=~450):
...
PD_REPORT v=1 stop_reason=complete chunks_returned=2 chunks_requested=2 chars_returned_total=1024 strong_hit=0 support=0
```

### With Evidence Stop
```bash
$ uv run trifecta ctx get -s . --ids prime:abc123,skill:xyz456 \
  --mode excerpt --stop-on-evidence --query Foo --pd-report --max-chunks 3

Retrieved 1 chunk(s) (mode=excerpt, tokens=~245):
...
PD_REPORT v=1 stop_reason=evidence chunks_returned=1 chunks_requested=2 chars_returned_total=512 strong_hit=1 support=1
```

## Use Cases

- **E2E Testing**: Validate early-stop behavior without parsing telemetry files
- **CI/CD**: Assert on specific `stop_reason` or chunk counts
- **Debugging**: Quick metrics without inspecting full telemetry
- **Automation**: Parse metrics for dashboards or alerts

## Parser Example

```python
# Parse PD_REPORT (order-independent)
for line in output.split("\n"):
    if line.startswith("PD_REPORT v="):
        metrics = {}
        for match in re.finditer(r"(\w+)=(\w+)", line):
            metrics[match.group(1)] = match.group(2)

        # Extract known keys (ignore unknown)
        version = int(metrics.get("v", 0))
        stop_reason = metrics.get("stop_reason")
        chunks_returned = int(metrics.get("chunks_returned", 0))
        # ... etc
```

## See Also

- [Progressive Disclosure](../README.md#progressive-disclosure)
- [Evidence-Based Early-Stop](../README.md#evidence-stop)
