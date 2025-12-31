### 3. Deterministic Build

`segment_id = normalize_segment_id(path.name)`
(strip, spaces->-, sanitize, lower, fallback)

- **Components Applying Rule**: `BuildContextPackUseCase (consumes TrifectaConfig.segment_id)`, `CLI (create/reset)`, `TrifectaConfig`.
- This prevents path drift.
- All filenames MUST use `_<segment_id>.md` suffix.

---
