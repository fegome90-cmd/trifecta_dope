# Trifecta CLI Workflow

**North Star**: The Trifecta CLI enables agents to programmatically call relevant context into their working memory using a **build-once, query-many** approach. Agents scaffold a segment, build a context pack, then search/retrieve chunks on-demand.

---

## Happy Path Workflow

### 1. Create Segment

**Command**:
```bash
trifecta create --segment <path>
```

**What it does**: Scaffolds a new Trifecta segment with required structure (`_ctx/prime_<segment>.md`, etc.)

**Preconditions**: None (creates new segment)

**Example**:
```bash
trifecta create --segment /tmp/my_segment
```

**Success**: Prints "Segment created" + files list

---

### 2. Sync Context (Build + Validate)

**Command**:
```bash
trifecta ctx sync --segment <path>
```

**What it does**: Macro that builds `context_pack.json` and validates it

**Preconditions**: 
- Segment must exist (created via `create`)
- `_ctx/prime_<segment>.md` must exist

**Example**:
```bash
trifecta ctx sync --segment /tmp/my_segment
```

**Success**: Prints "Build complete" + chunk count

**Error** (if prime missing):
```json
{
  "code": "SEGMENT_NOT_INITIALIZED",
  "message": "Segment not initialized. Run 'trifecta create -s <path>' first."
}
```

---

### 3. Search Context

**Command**:
```bash
trifecta ctx search --segment <path> --query "<question>"
```

**What it does**: Searches context pack for relevant chunks (RAG)

**Preconditions**:
- Context pack must exist (run `ctx sync` first)

**Example**:
```bash
trifecta ctx search --segment /tmp/my_segment --query "authentication flow"
```

**Success**: JSON with ranked chunks (`id`, `score`, `preview`)

---

### 4. Get Chunk Content

**Command**:
```bash
trifecta ctx get --segment <path> --ids <id1>,<id2>
```

**What it does**: Retrieves full content for specific chunk IDs

**Preconditions**:
- Context pack must exist
- Chunk IDs must be valid (from `ctx search` output)

**Example**:
```bash
trifecta ctx get --segment /tmp/my_segment --ids prime-1,skill-auth-2
```

**Success**: JSON with full content for each chunk

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

**Example**:
```bash
trifecta ast symbols "sym://python/mod/src.domain.result" --segment /tmp/my_segment
```

**Success**: JSON with symbols (`kind`, `name`, `line`)

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
trifecta create --segment /tmp/demo_segment

# Step 2: Sync (build + validate)
trifecta ctx sync --segment /tmp/demo_segment

# Step 3: Search for context
trifecta ctx search --segment /tmp/demo_segment --query "error handling"

# Step 4: Get specific chunks (use IDs from step 3)
trifecta ctx get --segment /tmp/demo_segment --ids prime-1,doc-error-3

# Step 5: Navigate code symbols (if applicable)
trifecta ast symbols "sym://python/mod/src.utils" --segment /tmp/demo_segment
```

---

## Common Error Cards

| Error Code | Next Steps |
|------------|------------|
| `SEGMENT_NOT_INITIALIZED` | Run `trifecta create -s <path>` |
| `FILE_NOT_FOUND` (AST) | Verify module path exists in segment |

---

## Telemetry Policy

- Default: Telemetry enabled (`_ctx/telemetry/`)
- Disable: Set `TRIFECTA_NO_TELEMETRY=1`
- Redirect: Set `TRIFECTA_TELEMETRY_DIR=<path>`

---

## CWD Policy

**Recommendation**: Run `uv run trifecta` from repository root (where `pyproject.toml` exists).

**Why**: `uv run` needs to find the project definition to activate the virtual environment correctly.
