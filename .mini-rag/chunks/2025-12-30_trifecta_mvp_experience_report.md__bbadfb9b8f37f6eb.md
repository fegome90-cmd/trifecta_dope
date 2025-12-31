### Fase 2: Build Context Pack
```bash
Command: uv run trifecta ctx build --segment .
Status: SUCCESS
Chunks Created: 7
Files Scanned: 7
Chunking Method: whole_file (para docs < 4K)
Time: ~3s
```

**Output Sample** (primeras líneas de stdout):
```
schema_version=1 segment='trifecta_dope' created_at='2025-12-30T16:35:21.137657'
source_files=[
  SourceFile(path='skill.md', sha256='5055ba...', mtime=1767099226.406185, chars=3541),
  SourceFile(path='_ctx/agent.md', sha256='327bb2...', mtime=1767099581.076171, chars=2905),
  ...
]
```
