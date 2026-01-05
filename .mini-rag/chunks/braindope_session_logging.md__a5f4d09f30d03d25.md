# Opción A: Filtro temprano con grep
grep '"cmd": "session.entry"' telemetry.jsonl | jq '...'
