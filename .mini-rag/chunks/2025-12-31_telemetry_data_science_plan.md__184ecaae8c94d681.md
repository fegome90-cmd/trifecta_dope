### Data Flow

1. **Capture (ya existe)**
   - Cada comando CLI → `Telemetry.event(cmd, args, result, timing)`
   - JSONL append-only con rotación

2. **Analysis Scripts (nuevos)**
   ```bash
   # Reporte rápido en terminal
   trifecta telemetry report

   # Exportar para análisis externo
   trifecta telemetry export --format json > data.json

   # Charts ASCII en terminal
   trifecta telemetry chart --type hits --days 7
   ```

3. **Agent Skill (nuevo)**
   - Skill: `telemetry-analyze`
   - Input: archivo de telemetry
   - Output: Markdown conciso con tablas

---
