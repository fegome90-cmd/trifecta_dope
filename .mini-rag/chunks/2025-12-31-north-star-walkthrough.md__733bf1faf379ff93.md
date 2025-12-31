### Type Safety

```bash
$ uv run mypy src/domain/result.py src/infrastructure/validators.py src/infrastructure/cli.py src/domain/models.py src/application/use_cases.py --strict
Success: no issues found in 5 source files
```
*(Includes `src/domain/models.py` for TrifectaConfig contract verification)*

---
