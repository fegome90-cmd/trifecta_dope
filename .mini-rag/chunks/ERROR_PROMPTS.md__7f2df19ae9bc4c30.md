### Python Harness (v1.1)

**v1.1 Features**:
- ✅ Real ID resolution from `context_pack.json`
- ✅ Typed numeric fields in PD_REPORT (int, not str)
- ✅ Deterministic fallback (pack → sync → error)

```bash
# Run harness on current segment
python scripts/harness_blackbox.py .

# Example output:
✅ Resolved IDs: ['skill:03ba77a5e8', 'prime:363a719791']
▶️  Running: uv run trifecta ctx get -s . --ids skill:03ba77a5e8,prime:363a719791 --pd-report
   ✅ Success
   📊 PD_REPORT: {'chunks_returned': 2, 'strong_hit': 0}  # Note: int, not str

# Output: _ctx/telemetry/harness_results.jsonl
```

**Note**: IDs are automatically resolved - no more hardcoded "prime:abc"!
