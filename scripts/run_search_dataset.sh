#!/bin/bash
set -euo pipefail

DATASET="${1:-docs/datasets/search_queries_v1.yaml}"

echo "🚀 Running Search Dataset v1 Runner..."
echo "Dataset: $DATASET"

uv run python3 scripts/runner_impl.py "$DATASET"

echo "📊 Running Parser..."
uv run python3 scripts/parse_search_logs.py

echo "✅ Done."