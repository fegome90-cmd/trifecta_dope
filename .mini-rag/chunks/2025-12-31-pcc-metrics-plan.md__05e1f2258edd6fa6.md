In `src/infrastructure/cli.py`:
- Load PRIME: `prime_*.md` from `_ctx` (choose expected one if available)
- Parse feature_map via `parse_feature_map`
- For each task result, compute PCC metrics using `evaluate_pcc`
- Print a new section:
  - `PCC Metrics:`
    - `path_correct_count`, `false_fallback_count`, `safe_fallback_count`

**Step 5: Run tests to verify pass**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py -v
```
Expected: PASS.

**Step 6: Commit**

```bash
git add src/infrastructure/cli.py src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC metrics to eval-plan"
```

---
