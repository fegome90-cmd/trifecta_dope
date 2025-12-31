## CLI Interface

```bash
# Generate context_pack.json in _ctx/
python ingest_trifecta.py --segment debug_terminal

# Custom output path
python ingest_trifecta.py --segment debug_terminal --output custom/pack.json

# Custom repo root
python ingest_trifecta.py --segment debug_terminal --repo-root /path/to/projects
```

**Default output**: `{segment}/_ctx/context_pack.json`

---
