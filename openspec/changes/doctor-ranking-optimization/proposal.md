# Proposal: doctor-ranking-optimization

## Intent
Fix the 3 ranking failures deferred by `doctor-issues-patch-batch-1`: `exit code drift`, `no me aparecen skills`, and `hub de skills`.

## Approach
Add a narrow exact-phrase doctor alias layer in `scripts/skill-hub`, reusing the existing canonical alias display path. Do not change BM25/FTS indexing in this batch.

## Success
The three phrases surface `skill-hub-doctor` as the visible canonical result while preserving original BM25 results as additional results.
