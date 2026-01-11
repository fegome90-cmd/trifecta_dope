### TAREA A: Error Classification Type-First ✅

| Antes | Después |
|-------|---------|
| Substring matching en cli.py | Type-based (`isinstance(e, PrimeFileNotFoundError)`) |
| Sin deprecation marker | Substring fallback marcado DEPRECATED |

**Tripwire**: `tests/unit/test_prime_file_not_found_error.py` (3 tests)
