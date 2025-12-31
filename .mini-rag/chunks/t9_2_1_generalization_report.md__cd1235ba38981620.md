## Stub Regeneration

**Implementation**: `src/application/stub_regen_use_case.py`
**Integration**: `ctx sync` now regenerates stubs after validation

| Stub | Max Lines | Actual Lines | Status |
|------|-----------|--------------|--------|
| repo_map.md | 300 | 60 | ✅ Within cap |
| symbols_stub.md | 200 | 29 | ✅ Within cap |

**Telemetry event**: `ctx.sync.stub_regen` with `regen_ok` and `reason` fields.

---
