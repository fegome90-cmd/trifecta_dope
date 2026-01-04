# Trifecta CLI Workflow

**North Star**: Trifecta enables agents to programmatically retrieve relevant context using build-once, query-many approach.

---

## Happy Path Workflow

### 1. Create Segment

**Command**:
```bash
trifecta create -s <path>
```

**What it does**: Scaffolds a new Trifecta segment with required files

**Preconditions**: None

**Example**:
```bash
trifecta create -s /tmp/my_segment
```

**Success**: Creates `_ctx/prime_<segment>.md`, `skill.md`, `readme_tf.md`, etc.

---

### 2. Sync Context (Build + Validate)

**Command**:
```bash
trifecta ctx sync -s <path>
```

**What it does**: Macro that builds `context_pack.json` and validates it

**Preconditions**:
- Segment must exist (created via `create`)
- `_ctx/prime_<segment>.md` must exist

**Example**:
```bash
trifecta ctx sync -s /tmp/my_segment
```

**Success**: Prints "Build complete" + chunk count, creates `_ctx/context_pack.json`

**Error** (if prime missing):
```
TRIFECTA_ERROR_CODE: SEGMENT_NOT_INITIALIZED
❌ TRIFECTA_ERROR: SEGMENT_NOT_INITIALIZED
CLASS: PRECONDITION
CAUSE: Missing prime file: /tmp/my_segment/_ctx/prime_my_segment.md

NEXT_STEPS:
  trifecta create -s /tmp/my_segment

VERIFY:
  trifecta ctx sync -s /tmp/my_segment
```

---

### 3. Search Context

**Command**:
```bash
trifecta ctx search -s <path> -q "<question>"
```

**What it does**: Searches context pack for relevant chunks

**Preconditions**:
- Context pack must exist (run `ctx sync` first)

**Options**:
- `-l <N>`: Max results (default: 5)
- `--telemetry <level>`: off/lite/full (default: lite)

**Example**:
```bash
trifecta ctx search -s /tmp/my_segment -q "authentication flow"
```

**Success**: Formatted text output with ranked chunks (score, preview, ID)

---

### 4. Get Chunk Content

**Command**:
```bash
trifecta ctx get -s <path> -i <id1>,<id2>
```

**What it does**: Retrieves full content for specific chunk IDs

**Preconditions**:
- Context pack must exist
- Chunk IDs must be valid (from `ctx search` output)

**Options**:
- `-m <mode>`: raw/excerpt/skeleton (default: excerpt)
- `-b <N>`: Max token budget (default: 1500)
- `--telemetry <level>`: off/lite/full (default: lite)

**Example**:
```bash
trifecta ctx get -s /tmp/my_segment -i prime-1,skill-auth-2
```

**Success**: Formatted text output with full content for each chunk

---

### 5. AST Symbols (Code Navigation)

**Command**:
```bash
trifecta ast symbols "sym://python/mod/<module.path>" --segment <path>
```

**What it does**: Returns AST symbols (functions, classes) from Python modules

**Preconditions**:
- Module file must exist in segment
- Python file must be parseable

**Options**:
- `--segment <path>`: Segment path (default: .)
- `--telemetry <level>`: off/lite/full (default: off)

**Example**:
```bash
trifecta ast symbols "sym://python/mod/src.domain.result" --segment /tmp/my_segment
```

**Success**: JSON with symbols

```json
{
  "status": "ok",
  "segment_root": "/tmp/my_segment",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 22},
    {"kind": "class", "name": "Err", "line": 53}
  ]
}
```

**Error** (if module not found):
```json
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for src.domain.result"
}
```

---

## Full Workflow Example (Copy/Paste)

```bash
# Step 1: Create segment
trifecta create -s /tmp/demo_segment

# Step 2: Sync (build + validate)
trifecta ctx sync -s /tmp/demo_segment

# Step 3: Search for context
trifecta ctx search -s /tmp/demo_segment -q "error handling"

# Step 4: Get specific chunks (use IDs from step 3 output)
trifecta ctx get -s /tmp/demo_segment -i prime-1,doc-error-3

# Step 5: Navigate code symbols (if Python files exist)
trifecta ast symbols "sym://python/mod/src.utils" --segment /tmp/demo_segment
```

---

## Common Error Behavior

| Error Code | Where | Output Format | Next Steps |
|------------|-------|---------------|------------|
| `SEGMENT_NOT_INITIALIZED` | ctx sync/search/get | Error Card (stderr) | Run `create -s <path>` |
| `FILE_NOT_FOUND` | ast symbols | JSON (stdout) | Verify module path exists |

---

## Telemetry Policy

**Default**: Telemetry enabled at `lite` level (`_ctx/telemetry/`)

**Environment Variables** (real):
- `TRIFECTA_NO_TELEMETRY=1`: Disable all telemetry
- `TRIFECTA_TELEMETRY_DIR=<path>`: Redirect telemetry output

**Per-command override** (where supported):
- `--telemetry off`: Disable for this invocation
- `--telemetry full`: Verbose telemetry
- `--telemetry lite`: Basic telemetry (default for most commands)

---

## CWD Policy

**Recommendation**: Run `uv run trifecta` from repository root (where `pyproject.toml` exists).

**Why**: `uv run` needs to find the project definition.

---

## Contract References

- **AST Symbols**: See `docs/contracts/AST_SYMBOLS_M1.md` for full JSON schema
- **Error Cards**: See `docs/ERROR_PROMPTS.md` for all error codes
