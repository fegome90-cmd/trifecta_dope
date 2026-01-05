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
