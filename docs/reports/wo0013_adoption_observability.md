# WO-0013: AST Persist Adoption Observability Report

## Evidence Header
- **WO**: WO-0013
- **SHA**: a6ae2848f4bea44e099a574ffd9887a77629f670
- **Analysis Date**: 2026-01-09
- **Data Source**: `_ctx/telemetry/events.jsonl`
- **Analysis Period**: 2026-01-02 to 2026-01-09 (7 days)
- **Method**: Telemetry event analysis via `analyze_adoption_telemetry.py`
- **Total Events Analyzed**: 3,751

---

## Executive Summary

Baseline analysis of AST cache persistence adoption shows **14% adoption rate** of FileLockedAstCache over the past 7 days, with **excellent cache effectiveness** (98.8% hit rate) and **minimal lock contention** (0 timeouts). The persistent cache is performing well for early adopters, with room for increased adoption.

### Key Findings
- **Adoption**: 14% of runs using FileLockedAstCache (525/3,751)
- **Performance**: 98.8% hit rate for persistent cache vs 0% for in-memory
- **Reliability**: Zero lock timeouts, only 6 lock waits in 7 days
- **Data Gap**: No cache database files detected (expected for worktree environment)

---

## Backend Distribution

| Backend | Runs | Percentage |
|---------|------|------------|
| **Unknown** | 3,212 | 85.6% |
| **FileLockedAstCache** | 525 | 14.0% |
| **InMemoryLRUCache** | 14 | 0.4% |
| **Total** | **3,751** | **100%** |

**Adoption Rate**: **14.0%** (FileLockedAstCache)

### Analysis
- 85.6% of events lack backend identifier (legacy telemetry or commands not triggering cache)
- FileLockedAstCache represents the majority of identified backend usage (14%)
- InMemoryLRUCache has minimal presence (0.4%) - likely fallback scenarios

---

## Cache Effectiveness

| Backend | Hit Rate | Hits | Misses | Total Operations |
|---------|----------|------|--------|------------------|
| **FileLockedAstCache** | **98.8%** | 513 | 6 | 519 |
| **InMemoryLRUCache** | **0.0%** | 0 | 7 | 7 |

### Key Insights
- **FileLockedAstCache**: Excellent hit rate (98.8%) indicates effective caching for persisted data
- **InMemoryLRUCache**: 0% hit rate suggests cold starts or eviction-prone workloads
- **Recommendation**: The high hit rate validates the persistence approach - more adoption would improve overall performance

---

## Lock Contention

| Metric | Value |
|--------|-------|
| **Total Lock Waits** | 6 |
| **Avg Wait Time** | 72.2 ms |
| **P50 Wait Time** | 56 ms |
| **P95 Wait Time** | 109 ms |
| **Max Wait Time** | 109 ms |
| **Timeouts** | 0 |
| **Timeout Rate** | 0.0% |

### Analysis
- **Minimal contention**: Only 6 lock waits across 7 days of usage
- **No timeouts**: Zero lock timeouts indicates well-tuned lock timeout values
- **Acceptable latency**: P95 wait time of 109ms is acceptable for AST cache operations
- **Healthy concurrency**: Lock contention is not a bottleneck for current adoption levels

---

## Database Growth

| Metric | Value |
|--------|-------|
| **DB Exists** | No |
| **Total Size** | 0 MB |
| **File Count** | 0 |

### Note
No cache database files detected in the worktree environment. This is expected since:
- Worktree is isolated from main development cache
- Database files would exist in active development segments
- Future analysis should target production/main branch segments

---

## Anomalies Detected

### 1. High "Unknown" Backend Count (85.6%)
**Severity**: LOW
**Description**: Majority of events lack backend identifier
**Likely Cause**:
- Legacy telemetry from commands not triggering cache backend selection
- Events from cache-agnostic operations (e.g., `ast.cache.hit` without backend context)
**Impact**: Limits visibility into true backend distribution
**Recommendation**: Update telemetry schema to consistently capture backend field

### 2. No Cache Database Files
**Severity**: INFO
**Description**: No `.trifecta/cache/ast_cache_*.db` files found
**Context**: Expected for isolated worktree environment
**Action Required**: Re-run analysis on main branch or production segment for DB growth metrics

---

## Recommendations

### Short-term (Next 1-2 Weeks)
1. **Increase Telemetry Coverage**: Ensure all cache-related events include `result.backend` field
2. **Production Baseline**: Run analysis on main branch segment to capture real DB growth
3. **Monitor Adoption**: Re-run analysis weekly to track FileLockedAstCache adoption trends

### Medium-term (Next 1-2 Months)
1. **Adoption Campaign**: Promote FileLockedAstCache usage given its excellent hit rate (98.8%)
2. **Hit Rate Monitoring**: Set up alerts if hit rate drops below 90% (indicates cache pollution or eviction issues)
3. **Lock Contention Tracking**: Monitor wait times as adoption increases (P95 currently 109ms)

### Long-term (3-6 Months)
1. **Cost-Benefit Analysis**: Compare FileLockedAstCache vs InMemoryLRUCache for different workload patterns
2. **Capacity Planning**: Project database growth based on adoption trends
3. **Performance Baseline**: Establish SLOs for hit rate (>95%) and lock contention (P95 < 200ms)

---

## Appendix: Full Metrics

See `_ctx/metrics/wo0013_adoption_baseline.json` for complete telemetry data.

### Analysis Period Details
- **Start**: 2026-01-02T19:20:33
- **End**: 2026-01-09T19:20:33
- **Duration**: 7 days
- **Segment Path**: `.worktrees/wo0013-ast-adoption-observability`

### Commands Analyzed
- `ast.symbols` - Backend distribution tracking
- `ast.cache.hit` - Cache hit events
- `ast.cache.miss` - Cache miss events
- `ast.cache.lock_wait` - Lock contention events
- `ast.cache.lock_timeout` - Lock timeout events
