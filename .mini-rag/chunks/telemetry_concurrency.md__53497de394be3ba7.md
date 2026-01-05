### Expected Results

- **Local dev (single process):** 0% drop rate
- **Parallel tests (10-50 processes):** 2-5% drop rate
- **Burst writes (100+ concurrent):** 5-10% drop rate (acceptable)
- **Pathological (saturated I/O):** >10% drop rate (needs investigation)

---
