# Negative Rejection Spec

Goal: detect false positives on out-of-domain queries.

Pass criteria:
- At least 4/5 queries return only irrelevant chunks.
- Fail if any query returns `docs/plans/*`, `docs/implementation/*`, or `_ctx/*` in top-5.

Notes:
- If a query returns only noise or empty results, mark PASS.
