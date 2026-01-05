### Step 2: Prepare (30 minutes)
```bash
cd /workspaces/trifecta_dope
git checkout -b feat/telemetry-instrumentation
pip install tree-sitter tree-sitter-python pytest pytest-cov
pytest tests/ -q  # Baseline
```
