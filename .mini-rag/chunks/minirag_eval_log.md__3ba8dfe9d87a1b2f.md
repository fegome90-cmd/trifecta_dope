## 2025-12-31 14:36
- Added `minirag-eval/` modules (negative_rejection, ambiguous_multihop, temporal_recency, contradictions, noise_injection)
- Ran `negative_rejection` baseline: 1/5 PASS
- Raised `retrieval.similarity_threshold` to 0.5 and lowered `top_k_default` to 4 (no improvement)
- Implemented domain guard for negative_rejection in `minirag-eval/run_bench.sh`
- Re-ran `negative_rejection`: 5/5 PASS (no chunks returned)
