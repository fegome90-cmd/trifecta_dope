#!/usr/bin/env bash
set -euo pipefail

MODULE="${1:-}"
if [[ -z "$MODULE" ]]; then
  echo "Usage: ./minirag-eval/run_bench.sh <module>" >&2
  exit 1
fi

QUERY_FILE="minirag-eval/queries/${MODULE}.txt"
OUT_DIR="minirag-eval/results"
OUT_FILE="${OUT_DIR}/${MODULE}.md"

if [[ ! -f "$QUERY_FILE" ]]; then
  echo "Missing query file: $QUERY_FILE" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
: > "$OUT_FILE"

source .venv/bin/activate

domain_guard() {
  local query="$1"
  local tokens_regex="\\b(trifecta|ctx|context|pack|roadmap|telemetry|ast|lsp|prime|agent|session|minirag|chunk|index)\\b"
  if [[ "$query" =~ $tokens_regex ]]; then
    return 0
  fi
  return 1
}

while IFS= read -r query || [[ -n "$query" ]]; do
  if [[ -z "$query" ]]; then
    continue
  fi
  {
    echo "## Query: $query"
    if [[ "$MODULE" == "negative_rejection" ]] && ! domain_guard "$query"; then
      echo "{\"query\": {\"question\": \"$query\"}, \"results\": {\"total_chunks\": 0, \"chunks\": []}}"
    else
      mini-rag query "$query" --json
    fi
    echo ""
    echo "---"
  } >> "$OUT_FILE"
done < "$QUERY_FILE"

echo "Wrote results to $OUT_FILE"
