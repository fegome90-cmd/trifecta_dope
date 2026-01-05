**Step 2: Run tests to confirm failure**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_requires_support_terms -v
uv run pytest tests/test_plan_use_case.py::test_l2_support_terms_telemetry_fields -v
```
Expected: FAIL (fields not present + config not honored yet).

**Step 3: Update aliases config**

Add to `_ctx/aliases.yaml` under `observability_telemetry`:
```yaml
    support_terms:
      - stats
      - metrics
      - events
      - jsonl
      - latency
      - p95
      - p50
      - flush
```

**Step 4: Implement config-driven support terms + telemetry**

Update `src/application/plan_use_case.py`:
- Remove hardcoded support_terms list
- For single-word triggers (priority >= 4), require `support_terms` in feature config
- If no support term present: fallback with warning `weak_single_word_trigger`
- Emit telemetry fields:
  - `l2_support_terms_required` (bool)
  - `l2_support_terms_present` (list)
  - `l2_weak_single_word_trigger` (bool)
  - `l2_clamp_decision` ("allow"|"block")

**Step 5: Run tests to confirm pass**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_requires_support_terms -v
uv run pytest tests/test_plan_use_case.py::test_l2_support_terms_telemetry_fields -v
```
Expected: PASS.

---
