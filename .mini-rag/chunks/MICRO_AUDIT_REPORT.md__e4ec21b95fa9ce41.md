### [P2] 7. Stringly-typed Chunk ID Parsing

- **Señal (command)**: `rg 'startswith\(|split\(' src/application`
- **Ubicación**: `src/application/context_service.py:28-29`, `src/application/use_cases.py:849-857`
- **Riesgo**: Chunk IDs parsed via `split(":", 1)` and `startswith("skill:")`. Adding new chunk types requires changes in multiple files.
- **Fix lean** (<= 60 líneas):
  Create `ChunkId` dataclass with `.kind` and `.name` properties:
  ```python
  @dataclass
  class ChunkId:
      kind: str  # "skill", "prime", "doc", etc.
      name: str

      @classmethod
      def parse(cls, raw: str) -> "ChunkId":
          parts = raw.split(":", 1)
          return cls(kind=parts[0].lower(), name=parts[1] if len(parts) > 1 else "")
  ```
- **Tripwire test**: `test_chunk_id_parse_exhaustive` (already exists in `tests/unit/test_chunk_id_parse.py`)
- **Evidencia requerida**: `pytest tests/unit/test_chunk_id_parse.py -v`

---
