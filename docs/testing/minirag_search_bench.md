# Mini-RAG Search Bench (Manual)

Goal: calibrate search quality for docs/plans/research by running a stable set of
queries and checking if expected sources appear in top-k.

## Prereqs

```bash
make minirag-chunk
make minirag-index
```

## How to Run

Option A (manual):

```bash
. .venv/bin/activate
mini-rag query "implementacion de ast" --json
```

Option B (batch helper):

```bash
./scripts/minirag_bench_run.sh
```

Results are written to `docs/testing/minirag_search_bench_results.md`.

## Query Set + Expected Signals

1) Query: "implementacion de ast"  
Expected: top-3 includes `docs/integracion-ast-agentes.md` (via chunk source).

2) Query: "ast parser referencia"  
Expected: top-5 includes a chunk that mentions `legacy/ast-parser.ts`.

3) Query: "implementacion de lsp"  
Expected: top-3 includes `docs/2025-12-29-trifecta-context-loading.md`.

4) Query: "go to definition hover lsp"  
Expected: top-3 includes a chunk describing LSP definition/hover usage.

5) Query: "context pack ingestion schema v1 digest index chunks"  
Expected: top-5 includes `docs/plans/2025-12-29-context-pack-ingestion.md`.

6) Query: "trifecta ctx validate command"  
Expected: top-5 includes a chunk mentioning `trifecta ctx validate`.

7) Query: "progressive disclosure L0 L1 L2"  
Expected: top-5 includes a chunk mentioning "L0/L1/L2" tiers.

8) Query: "chunking fences headings"  
Expected: top-5 includes chunking description with fences/headings language.

## Adversarial / Stress Queries

9) Query: "skeletonizer tree-sitter ast parser"  
Expected: top-5 includes `docs/plans/2025-12-29-trifecta-context-loading.md`.

10) Query: "lsp diagnostics hot files"  
Expected: top-5 includes LSP diagnostics section (context-loading plan).

11) Query: "workspace symbols lsp search"  
Expected: top-5 includes LSP `workspace_symbols` usage.

12) Query: "progressive disclosure hooks L0 L1 L2"  
Expected: top-5 includes Progressive Disclosure L0/L1/L2 or hooks mention.

13) Query: "context pack json schema_version"  
Expected: top-5 includes context pack schema description.

14) Query: "ctx search get excerpt budget"  
Expected: top-5 includes `ctx.search`/`ctx.get` budget usage.

15) Query: "ollama keep_alive retry_delay config"  
Expected: top-5 includes `.mini-rag/config.yaml` values or discussion.

16) Query: "index embeddings.npy metadata.json"  
Expected: top-5 includes index file descriptions.

## Negative Rejection Queries

17) Query: "politica de vacaciones del equipo"  
Expected: top-5 should NOT include any Trifecta planning or context docs.

18) Query: "receta de pasta carbonara"  
Expected: top-5 should be clearly irrelevant or empty; mark FAIL if it returns core docs.

19) Query: "resultados de las elecciones 2024 en Francia"  
Expected: top-5 should be irrelevant; mark FAIL if it returns core Trifecta docs.

20) Query: "guia de cultivo de tomates en casa"  
Expected: top-5 should be irrelevant; mark FAIL if it returns core Trifecta docs.

21) Query: "manual de usuario de iphone 15"  
Expected: top-5 should be irrelevant; mark FAIL if it returns core Trifecta docs.

## Pass/Fail Criteria

- Pass = at least 12 of 16 queries satisfy the expected signal in top-5.
- If fail, adjust only one knob at a time and re-run.

## Negative Rejection Criteria

- Pass = 4 of 5 negative queries return only irrelevant chunks.
- Fail if any negative query returns `docs/plans/*`, `docs/implementation/*`, or `_ctx/*` in top-5.

## Calibration Knobs (in .mini-rag/config.yaml)

- retrieval.top_k_default (raise to 10-12 if results are thin)
- retrieval.similarity_threshold (raise to reduce noise, lower to improve recall)
- docs_glob (scope to reduce unrelated docs)
- chunking.section_max_chars / chunking.chunk_size (coherence vs. granularity)

## Results Log (template)

```
Run: YYYY-MM-DD HH:MM
Index: fresh (yes/no)
Changes since last run: <one line>

Query 1: PASS/FAIL - notes
Query 2: PASS/FAIL - notes
...
Query 8: PASS/FAIL - notes
```
