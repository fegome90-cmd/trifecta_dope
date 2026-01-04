#!/bin/bash
# Quick launch script for Trifecta Telemetry Analysis Jupyter Notebook

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔬 Trifecta Telemetry Analysis"
echo "=============================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Validate we're in a Trifecta project
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "_ctx" ]]; then
    echo "❌ Error: Not a valid Trifecta project directory"
    echo "   Expected: pyproject.toml and _ctx/ directory"
    echo "   Current: $(pwd)"
    exit 1
fi

# Check if telemetry dependencies are installed
if ! uv run python -c "import plotly, pandas, kaleido" 2>/dev/null; then
    echo "⚠️  Telemetry dependencies not found!"
    echo "   Installing with: uv sync --extra telemetry"
    uv sync --extra telemetry
fi

# Launch Jupyter notebook
echo "🚀 Launching Jupyter notebook..."
uv run jupyter notebook telemetry_analysis/Trifecta_Telemetry_Analysis.ipynb
