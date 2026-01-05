5. **Restricción**: NO paths absolutos en outputs (privacy/portability)
   Razón: Privacy - leaked /Users/username en logs expone PII
   Test que valida:
   ```bash
   uv run trifecta session query -s . --last 1 | rg "/Users/|/home/" && exit 1 || exit 0
   ```
   CI gate: `tests/acceptance/test_no_absolute_paths.py`

---
