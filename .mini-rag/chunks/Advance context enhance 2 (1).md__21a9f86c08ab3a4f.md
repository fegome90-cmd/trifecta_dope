### Context Pack Schema v1

Each project has its own context directory:

```
/projects/<segment>/
  _ctx/
    context_pack.json
    context.db          # phase 2
    autopilot.log
    .autopilot.lock
  skill.md
  prime.md
  agent.md
  session.md
```

The `context_pack.json` contains:

```json
{
  "schema_version": 1,
  "created_at": "2025-01-15T10:30:00Z",
  "generator_version": "trifecta-0.1.0",
  "source_files": [
    {
      "path": "skill.md",
      "sha256": "abc123...",
      "mtime": "2025-01-15T09:00:00Z",
      "chars": 5420
    }
  ],
  "chunking": {
    "method": "heading_aware",
    "max_chunk_tokens": 600
  },
  "digest": "Short summary of context...",
  "index": [
    {
      "id": "skill:a8f3c1",
      "doc": "skill.md",
      "title_path": ["Commands", "Build"],
      "token_est": 120
    }
  ],
  "chunks": [
    {
      "id": "skill:a8f3c1",
      "doc": "skill.md",
      "title_path": ["Commands", "Build"],
      "text": "...",
      "token_est": 120,
      "text_sha256": "def456..."
    }
  ]
}
```

**Key properties**:

- Stable IDs via deterministic hashing: `doc + ":" + sha1(doc + title_path_norm + text_sha256)[:10]`
- Fence-aware chunking: doesn’t split code blocks mid-fence
- Zero cross-contamination between projects
