# HN Benchmark Methodology

## Task Specification
**Task**: Retrieve the implementation and logic of `ValidateContextPackUseCase` to understand how it verifies context packs.
**Goal**: Verify that the correct code chunk containing `class ValidateContextPackUseCase` is retrieved.

## Acceptance Criteria
- **PASS**: The retrieved context contains the definition of `class ValidateContextPackUseCase` (in `src/application/use_cases.py` or `src/application/search_get_usecases.py` if moved, currently in `src/application/use_cases.py`).
- **FAIL**: The class definition is missing from the retrieved context.

## Scenarios

### A) Baseline: Context Dumping
- **Method**: Load all Python files in `src/` into the context.
- **Metrics**:
  - `tokens_in`: Total tokens of all `src/**/*.py` files.
  - `wall_time`: Time to read and tokenize all files.
  - `cost`: Estimated based on `tokens_in` ($3.00/1M tokens).

### B) CLI: Programmatic Context Calls (PCC)
- **Method**:
  1. Execute `trifecta ctx search --query "ValidateContextPackUseCase"`.
  2. Identify the chunk ID for `src/application/use_cases.py`.
  3. Execute `trifecta ctx get --ids <chunk_id>`.
- **Metrics**:
  - `tokens_in`: Tokens from search results + tokens from `ctx.get` output.
  - `wall_time`: Sum of wall time for `search` and `get` commands.
  - `tool_calls`: 2 (1 search, 1 get).
  - `cost`: Estimated based on `tokens_in` ($3.00/1M tokens).

## Run Parameters
- **N**: 10 trials per scenario.
- **Model**: Simulated (Deterministic retrieval).
- **Environment**:
  - **OS**: Linux (Container)
  - **Filesystem**: Local SSD
  - **Corpus Revision**: `ceaf20c62377dfa84a1eb62cb9516ef66b2cfd84`
- **Cost Model**: $3.00 per 1M input tokens (approx. Claude 3.5 Sonnet pricing).

## Definitions
- **tokens_in**: Counted using `tiktoken` (encoding: `cl100k_base`).
- **wall_time**: Python `time.perf_counter()` duration.
- **Zero-hit**: A `ctx.search` call returning 0 results (CLI only).
