## B) Schema v1

```json
{
  "schema_version": 1,
  "segment_id": "debug_terminal",
  "created_at": "2025-12-31T15:00:00Z",
  "source_files": [
    {"path": "skill.md", "sha256": "abc...", "chars": 2500}
  ],
  "digest": [
    {"doc": "skill", "chunk_id": "skill:a1b2c3d4e5", "summary": "Core rules..."}
  ],
  "index": [
    {"id": "skill:a1b2c3d4e5", "doc": "skill", "title": "Core Rules", "token_est": 625}
  ],
  "chunks": [
    {"id": "skill:a1b2c3d4e5", "doc": "skill", "title": "Core Rules", "text": "# Core...", "token_est": 625}
  ]
}
```

**ID Format:** `{doc}:{sha256(text)[:10]}`  
**Errors:** `"Context pack not found at {path}"`, `"Context pack is invalid JSON"`, `"Chunk not found: {id}"`

---
