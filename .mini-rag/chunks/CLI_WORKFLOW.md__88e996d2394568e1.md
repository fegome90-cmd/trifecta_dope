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
