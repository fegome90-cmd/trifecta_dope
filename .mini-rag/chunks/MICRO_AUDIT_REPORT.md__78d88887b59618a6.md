### [P2] 8. Segment Resolution via `resolve()` Everywhere

- **Señal (command)**: `rg 'resolve\(\)' src/infrastructure`
- **Ubicación**: `src/infrastructure/cli.py` (15 occurrences), `src/infrastructure/segment_utils.py:13-36`
- **Riesgo**: `Path.resolve()` called on nearly every CLI command entry. Symlinks may resolve unexpectedly. No central "resolved once, pass around" pattern.
- **Fix lean** (<= 60 líneas):
  Create `ResolvedSegment` newtype wrapper that guarantees resolution happened once:
  ```python
  class ResolvedSegment(Path):
      """A segment path that has been resolved exactly once."""
      @classmethod
      def from_raw(cls, raw: str) -> "ResolvedSegment":
          return cls(Path(raw).resolve())
  ```
  Update CLI handlers to accept `ResolvedSegment`.
- **Tripwire test**: `test_resolved_segment_is_absolute`
- **Evidencia requerida**: `rg 'resolve\(\)' src/infrastructure --count`

---
