### Schema v1 ✅
- **schema_version**: `int` (v1).
- **ID Estable**: `doc:sha1(doc+text)[:10]`.
- **Source Tracking**: `source_files[]` con paths, SHA256, mtime y tamaño.
- **Validation**: Invariantes (Index IDs ⊆ Chunks IDs).
