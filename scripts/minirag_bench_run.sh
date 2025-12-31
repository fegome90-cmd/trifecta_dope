#!/usr/bin/env bash
set -euo pipefail

QUERY_FILE="${1:-docs/testing/minirag_search_bench_queries.txt}"
OUT_FILE="${2:-docs/testing/minirag_search_bench_results.md}"

if [[ ! -f "$QUERY_FILE" ]]; then
  echo "Missing query file: $QUERY_FILE" >&2
  exit 1
fi

: > "$OUT_FILE"

source .venv/bin/activate

while IFS= read -r query || [[ -n "$query" ]]; do
  if [[ -z "$query" ]]; then
    continue
  fi
  {
    echo "## Query: $query"
    mini-rag query "$query" --json
    echo ""
    echo "---"
  } >> "$OUT_FILE"
done < "$QUERY_FILE"

echo "Wrote results to $OUT_FILE"
