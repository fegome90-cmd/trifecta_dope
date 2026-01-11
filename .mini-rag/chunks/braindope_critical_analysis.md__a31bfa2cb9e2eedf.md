### 6. **Tool Use Detection - ¿Quién Parsea?**

**PROPUESTA**: "se puede identificar con el post tool use"

**PROBLEMA**: ¿Quién parsea tool use?
- ¿El agente? (añade latencia al workflow)
- ¿El script background? (necesita acceso al contexto del agente)
- ¿El CLI? (necesita info que no tiene)

**REALIDAD**: `trifecta session append` recibe `--files` y `--commands` manualmente. No hay auto-detección de tool use actualmente.

**COSTO**: Implementar auto-detección = parsear output del agente = complejo y frágil.

---
