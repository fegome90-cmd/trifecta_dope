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
