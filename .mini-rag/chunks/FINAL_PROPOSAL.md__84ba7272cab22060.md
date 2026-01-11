### Telemetry Rotation (automática)
```bash
# Script ejecutado por `trifecta ctx sync` si telemetry > 10K events
if [ $(wc -l < telemetry/events.jsonl) -gt 10000 ]; then
  # Move events older than 30 days to archive
  awk -v cutoff=$(date -d '30 days ago' +%s) '...' \
    telemetry/events.jsonl > telemetry/archive_$(date +%Y%m).jsonl
fi
```

**Resultado**: telemetry activo siempre < 10K events → queries < 50ms

---
