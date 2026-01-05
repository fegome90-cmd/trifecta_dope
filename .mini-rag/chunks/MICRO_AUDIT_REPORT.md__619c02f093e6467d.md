### [P2] 10. Lower-case String Comparisons Scattered

- **Señal (command)**: `rg 'lower\(\)' src/application`
- **Ubicación**: `context_service.py` (8 occurrences), `use_cases.py` (5), `plan_use_case.py` (9)
- **Riesgo**: Case-insensitive comparisons done via `.lower()` ad-hoc. Locale issues possible, no central normalization.
- **Fix lean** (<= 60 líneas):
  Create `normalize_query(q: str) -> str` helper that does `.lower().strip()` once.
  Already partially exists in `query_normalizer.py` but not used everywhere.
- **Tripwire test**: `test_query_normalizer_used_for_search`
- **Evidencia requerida**: `pytest tests/unit/test_query_normalizer.py -v`

---
