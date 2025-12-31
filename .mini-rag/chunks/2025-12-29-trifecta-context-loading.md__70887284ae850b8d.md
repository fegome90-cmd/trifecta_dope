### Structure (MVP)
```json
{
  "schema_version": 1,
  "segment": "debug-terminal",
  "created_at": "...",
  "source_files": [
    {"path": "skill.md", "sha256": "...", "mtime": 123.4, "chars": 2500}
  ],
  "chunks": [
    {
      "id": "skill:24499e07a2",
      "doc": "skill",
      "title_path": ["skill.md"],
      "text": "# Debug Terminal - Skill\n...",
      "char_count": 2500,
      "token_est": 625,
      "source_path": "skill.md",
      "chunking_method": "whole_file"
    }
  ],
  "index": [
    {
      "id": "skill:24499e07a2",
      "title_path_norm": "skill.md",
      "preview": "# Debug Terminal - Skill...",
      "token_est": 625
    }
  ]
}
```

**Más adelante**: Cambiar a `headings+fence_aware` sin romper la interfaz.

---
