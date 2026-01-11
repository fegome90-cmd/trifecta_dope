### Deterministic (No LLM needed)

Recovery steps are **deterministic** based on error code:

| Error Code | Pattern |
|------------|---------|
| `SEGMENT_NOT_INITIALIZED` | create → verify → sync |
| `PRIME_FILE_NOT_FOUND` | check structure → refresh-prime → verify |
| Generic | check syntax → verify init → review cause |
