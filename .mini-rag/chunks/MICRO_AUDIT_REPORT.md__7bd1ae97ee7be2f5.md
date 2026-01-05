### [P0] 1. Stringly-typed PrimeFileNotFoundError Classification

- **Señal (command)**: `rg 'in str\(e\)|"Expected .* not found"' src tests`
- **Ubicación**: `src/infrastructure/cli.py:992`, `tests/unit/test_type_priority.py:23,28`
- **Riesgo**: Error classification uses substring matching (`"Expected prime file not found" in str(e)`). Refactoring the error message breaks the error card routing silently. CI passes but wrong error is shown to user.
- **Fix lean** (<= 60 líneas):
  ```python
  # Replace string matching with type check:
  except PrimeFileNotFoundError as e:
      return render_error_card("SEGMENT_NOT_INITIALIZED", ...)
  except FileNotFoundError as e:  # Generic fallback
      ...
  ```
  Remove the `TRIFECTA_DEPRECATED: fallback_prime_missing_string_match_used` path once type-based routing is 100%.
- **Tripwire test**: `test_error_classification_by_type_not_string`
  ```python
  def test_error_classification_by_type_not_string():
      # Raise PrimeFileNotFoundError with a DIFFERENT message
      # Assert error card code is still SEGMENT_NOT_INITIALIZED
  ```
- **Evidencia requerida**: `pytest tests/unit/test_type_priority.py -v`

---
