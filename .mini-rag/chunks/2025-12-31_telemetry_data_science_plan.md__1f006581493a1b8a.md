### Phase 3: SQLite Analytics (opcional, 1-2 horas)

| Task | Archivo | Descripción |
|------|---------|-------------|
| 3.1 | `scripts/etl_telemetry.py` | JSONL → SQLite ETL |
| 3.2 | `src/infrastructure/telemetry_db.py` | SQLite schema y queries |

**SQLite Schema**:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    command TEXT NOT NULL,
    args_json TEXT,
    result_json TEXT,
    timing_ms INTEGER
);

CREATE INDEX idx_command ON events(command);
CREATE INDEX idx_timestamp ON events(timestamp);
```

---
