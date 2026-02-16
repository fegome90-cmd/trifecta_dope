# Telemetry Epoch: 2026-02-15

## Epoch Marker
- **Started**: 2026-02-15 21:15 UTC-3
- **Reason**: Index rebuild (context_pack.json regenerated)
- **Commit**: f218cc3bac1462caa54002305bc59a8bb59c15eb
- **Segment Fingerprint**: 6f25e381

## Previous Epoch Metrics (Pre-Rebuild Baseline)

### Zero-Hit Ratios
| Source | Zero-Hits | Searches | Ratio |
|--------|-----------|----------|-------|
| unknown | 185 | 714 | 25.9% |
| fixture | 132 | 564 | 23.4% |
| interactive | 100 | 583 | 17.2% |
| **Operational (excl. fixture)** | 285 | 1297 | **22.0%** |
| **Overall** | 417 | 1861 | 22.4% |

### Spanish Alias Impact
- **Applied**: 41
- **Recovered**: 41
- **Recovery Rate**: 100%
- **Top Aliases**: servicio (28), búsqueda (13), servicios (13)

### Top Zero-Hit Queries (Historical)
1. servicio (12)
2. servicios (12)
3. búsqueda (12)
4. services (12)
5. stop_reason (12)

## New Epoch
- Fresh telemetry initialized
- All previous data archived to `_ctx/telemetry/archive/`
- Health commands now measure only current epoch data

## Analysis Notes
- The 22% zero-hit ratio was based on events before index rebuild
- After rebuild, sample searches (ContextService, telemetry, test, search, skill) all returned hits
- The index improved, making historical zero-hits now findable

## Archive Files
Located in `_ctx/telemetry/archive/`:
- `events_20260215_pre_rebuild.jsonl`
- `zero_hits_20260215_pre_rebuild.ndjson`
