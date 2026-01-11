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
