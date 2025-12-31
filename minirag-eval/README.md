# Mini-RAG Eval Packs

Purpose: keep advanced retrieval test sets isolated from core docs and configs.

Structure:
- `minirag-eval/queries/` query sets by module
- `minirag-eval/specs/` expectations and pass/fail criteria
- `minirag-eval/results/` outputs (not committed)
- `minirag-eval/run_bench.sh` helper to run a module

## Modules

- negative_rejection
- ambiguous_multihop
- temporal_recency
- contradictions
- noise_injection

## Run

```bash
./minirag-eval/run_bench.sh negative_rejection
./minirag-eval/run_bench.sh ambiguous_multihop
```

Results are written to `minirag-eval/results/<module>.md`.
