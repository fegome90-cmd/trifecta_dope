### Deliverables

1. **`scripts/ingest_trifecta.py`** - Full context pack builder
   - Fence-aware chunking
   - Deterministic digest (scoring)
   - Stable IDs (normalized hash)
   - Complete metadata

2. **Tests**
   - Snapshot test: same input → same output
   - Stability test: change in doc A doesn't affect IDs in doc B
