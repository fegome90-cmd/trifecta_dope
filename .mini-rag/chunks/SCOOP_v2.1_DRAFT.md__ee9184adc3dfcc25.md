3. **Anti-goal**: "NO optimizar para archivos grandes"
   Justificación: El proyecto asume docs curados (<5K tokens). Session.md grande viola North Star.
   Features que PERMANECEN: session.md como log humano, pero debe mantenerse ligero vía archivado o generación desde JSONL
   Test que valida:
   ```bash
   # Session.md debe ser < 2000 líneas (umbral soft)
   wc -l _ctx/session_*.md | awk '{if ($1 > 2000) exit 1}'
   ```

---
