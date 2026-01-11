### Query Rápido (grep first)
```bash
# Implementación interna de `trifecta session query`
grep '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | \
  jq -c 'del(.run_id, .segment_id, .timing_ms, .warnings) |
         {ts, summary: .args.summary, type: .args.type,
          files: .args.files, commands: .args.commands,
          outcome: .result.outcome, tags: .x.tags}'
```

**Performance**: ~30-50ms para 50K events (grep elimina 99% antes de jq)
