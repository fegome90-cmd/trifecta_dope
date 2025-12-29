# Trifecta Context Pack - Implementation Plan

**Date**: 2025-12-29
**Status**: Design Complete
**Schema Version**: 1

---

## Overview

Design and implement a token-optimized Context Pack system for Trifecta documentation. The system generates a structured JSON pack from markdown files, enabling LLMs to ingest documentation context efficiently without loading full texts into prompts.

## Problem Statement

Current approaches to loading context for code agents have two fundamental issues:

1. **Inject full markdown** → Burns tokens on every call, doesn't scale
2. **Unstructured context** → No index, no way to request specific chunks

**Solution**: 3-layer Context Pack (Digest + Index + Chunks) delivered on-demand via tools.

---

## Architecture

### 3-Layer Context Pack

```
┌─────────────────────────────────────────────────────────────┐
│  context_pack.json (written to disk)                        │
├─────────────────────────────────────────────────────────────┤
│  {                                                         │
│    "schema_version": 1,                                    │
│    "segment": "debug_terminal",                            │
│    "digest": [              // ALWAYS in prompt (~10-30 lines)│
│      {"doc": "skill", "summary": "...", "source_chunk_ids": [...]}│
│    ],                                                      │
│    "index": [               // ALWAYS in prompt (chunk refs)  │
│      {"id": "skill:a1b2...", "title_path": ["Core Rules"], ...}│
│    ],                                                      │
│    "chunks": [              // DELIVERED ON-DEMAND         │
│      {"id": "skill:a1b2...", "text": "...", ...}            │
│    ]                                                       │
│  }                                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Runtime Tool (HemDov/Agent) - SEPARATED from pack          │
├─────────────────────────────────────────────────────────────┤
│  get_context(chunk_id) → chunk["text"]                     │
│  search_context(query, k) → [chunk_id, ...]  // Phase 2      │
└─────────────────────────────────────────────────────────────┘
```

### Isolation by Project

Each Trifecta segment has its own isolated context:

```
/projects/
├── debug_terminal/
│   ├── _ctx/
│   │   ├── context_pack.json    # Only for debug_terminal
│   │   └── context.db           # SQLite: only debug_terminal chunks (Phase 2)
│   └── skill.md
├── eval/
│   ├── _ctx/
│   │   ├── context_pack.json    # Only for eval
│   │   └── context.db           # SQLite: only eval chunks
│   └── skill.md
```

**No cross-contamination** between projects.

---

## Schema v1 Specification

```json
{
  "schema_version": 1,
  "segment": "string",
  "created_at": "ISO8601",
  "generator_version": "0.1.0",
  "source_files": [
    {
      "path": "skill.md",
      "sha256": "hex",
      "mtime": 1234567890,
      "chars": 2500,
      "size": 2500
    }
  ],
  "chunking": {
    "method": "headings+paragraph_fallback+fence_aware",
    "max_chars": 6000
  },
  "docs": [
    {
      "doc": "skill",
      "file": "skill.md",
      "sha256": "hex",
      "chunk_count": 3,
      "total_chars": 2500
    }
  ],
  "digest": [
    {
      "doc": "skill",
      "summary": "Core Rules → Sync First, Test Locally...",
      "source_chunk_ids": ["skill:a1b2c3d4e5", "skill:f6e7d8c9b0"]
    }
  ],
  "index": [
    {
      "id": "skill:a1b2c3d4e5",
      "doc": "skill",
      "title_path": ["Core Rules"],
      "preview": "Sync First: Validate .env...",
      "token_est": 150,
      "source_path": "skill.md",
      "heading_level": 2,
      "char_count": 450,
      "line_count": 12,
      "start_line": 31,
      "end_line": 43
    }
  ],
  "chunks": [
    {
      "id": "skill:a1b2c3d4e5",
      "title_path": ["Core Rules"],
      "text": "1. **Sync First**: Valida...",
      "source_path": "skill.md",
      "heading_level": 2,
      "char_count": 450,
      "line_count": 12,
      "start_line": 31,
      "end_line": 43
    }
  ]
}
```

---

## Implementation Details

### 1. Fence-Aware Chunking

**Problem**: Headings inside code blocks (``` fence) should not create chunks.

**Solution**: State machine tracking `in_fence`:

```python
in_fence = False
for line in lines:
    if line.strip().startswith(("```", "~~~")):
        in_fence = not in_fence
    elif HEADING_RE.match(line) and not in_fence:
        # New chunk
```

### 2. Digest Determinista (Scoring)

**Problem**: "First 800 chars" is not semantic quality.

**Solution**: Score-based selection of top-2 chunks per doc:

```python
def score_chunk(title: str, level: int, text: str) -> int:
    score = 0
    title_lower = title.lower()

    # Keywords that indicate relevance
    if any(kw in title_lower for kw in ["core", "rules", "workflow", "commands",
                                            "usage", "setup", "api", "architecture"]):
        score += 3

    # Higher headings are more important
    if level <= 2:
        score += 2

    # Penalize empty overview/intro
    if kw in ["overview", "intro"] and len(text) < 300:
        score -= 2

    return score

# Take top-2 chunks by score per doc, max 1200 chars total
```

### 3. Stable IDs via Normalization

**Problem**: Sequential IDs (`skill:0001`) break on insert. Raw hash changes on whitespace.

**Solution**: Normalized components + hash:

```python
def normalize_title_path(path: list[str]) -> str:
    return "\x1f".join(p.strip().lower().collapse_spaces() for p in path)

def generate_chunk_id(doc: str, title_path: list[str], text: str) -> str:
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    seed = f"{doc}\n{normalize_title_path(title_path)}\n{text_hash}"
    return hashlib.sha1(seed.encode()).hexdigest()[:10]

# Result: "skill:a1b2c3d4e5"
```

### 4. Preview Generation

```python
def preview(text: str, max_chars: int = 180) -> str:
    one_liner = re.sub(r"\s+", " ", text.strip())
    return one_liner[:max_chars] + ("…" if len(one_liner) > max_chars else "")
```

### 5. Token Estimation

```python
def estimate_tokens(text: str) -> int:
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4
```

---

## CLI Interface

```bash
# Generate context_pack.json in _ctx/
python ingest_trifecta.py --segment debug_terminal

# Custom output path
python ingest_trifecta.py --segment debug_terminal --output custom/pack.json

# Custom repo root
python ingest_trifecta.py --segment debug_terminal --repo-root /path/to/projects
```

**Default output**: `{segment}/_ctx/context_pack.json`

---

## Phase 1: MVP (Today)

### Deliverables

1. **`scripts/ingest_trifecta.py`** - Full context pack builder
   - Fence-aware chunking
   - Deterministic digest (scoring)
   - Stable IDs (normalized hash)
   - Complete metadata

2. **Tests**
   - Snapshot test: same input → same output
   - Stability test: change in doc A doesn't affect IDs in doc B

### Exit Criteria

- ✅ Generates valid `context_pack.json` schema v1
- ✅ Digest uses top-2 relevant chunks (not first chars)
- ✅ IDs are stable across runs
- ✅ Code fences are respected
- ✅ Tests pass

---

## Phase 2: SQLite Runtime (Future)

When context packs grow large:

1. **`context.db`** (SQLite per project)
   ```sql
   CREATE TABLE chunks (
     id TEXT PRIMARY KEY,
     doc TEXT,
     title_path TEXT,
     text TEXT,
     source_path TEXT,
     heading_level INTEGER,
     char_count INTEGER,
     line_count INTEGER,
     start_line INTEGER,
     end_line INTEGER
   );
   CREATE INDEX idx_chunks_doc ON chunks(doc);
   CREATE INDEX idx_chunks_title_path ON chunks(title_path);
   ```

2. **Runtime Tools**
   - `get_context(id)` → O(1) lookup
   - `search_context(query, k)` → BM25 or full-text search

3. **JSON changes**
   - Keep `index` and metadata in JSON
   - Move `chunks.text` to SQLite (or separate files)

---

## Critical Fixes Applied

| # | Issue | Fix |
|---|-------|-----|
| 1 | Digest quality | Scoring system instead of first-N chars |
| 2 | ID instability | Normalized hash instead of sequential |
| 3 | Code fence corruption | State machine tracking `in_fence` |
| 4 | Missing metadata | Added source_path, char_count, line_count, etc. |
| 5 | Runtime O(n) lookup | Prepared for SQLite in Phase 2 |
| 6 | No contract | Schema versioning + manifest |

---

## Success Criteria

- [ ] Schema v1 defined and documented
- [ ] Fence-aware chunking working
- [ ] Digest uses scoring (top-2 chunks)
- [ ] IDs are deterministic and stable
- [ ] All metadata fields present
- [ ] Snapshot test passing
- [ ] Stability test passing
- [ ] Works with any Trifecta segment (project-agnostic)

---

## References

- Original plan: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plan-script.md`
- Implementation: `scripts/ingest_trifecta.py`
- Tests: `tests/test_context_pack.py` (to be created)
