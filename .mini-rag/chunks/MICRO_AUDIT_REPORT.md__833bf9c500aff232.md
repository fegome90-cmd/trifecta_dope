## Lista de tests con SKIP/XFAIL

| File | Skip/XFail Count | Reason | Propuesta de reemplazo |
|------|-----------------|--------|----------------------|
| `test_pd_evidence_stop_e2e.py` | 9 `pytest.skip()` | Precondition failures | Use fail-closed fixture with known-good segment |
| `test_segment_id_invariants.py` | 2 `pytest.skip()` | No events.jsonl | Create fixture that generates telemetry |
| `test_prime_tripwires.py` | 2 `pytest.skip()` | Prime file missing | Include in segment creation fixture |
| `test_prime_paths_only.py` | 1 `pytest.skip()` | Prime file not found | Same as above |
| `test_prime_top10_in_pack.py` | 1 `pytest.skip()` | Prime file missing | Same as above |
| `test_plan_use_case.py` | 1 `pytest.skip()` | `_ctx/generated/` missing | Create in fixture or use `tmp_path` |
| `test_cli_smoke_real_use.py` | 1 `@pytest.mark.skip` | Parallel execution | Convert to proper parametrization |

**Total**: 17 skip sites across 7 files.

---
