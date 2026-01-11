### 4. **Schema Evolution y Backwards Compatibility**

**PROBLEMA**: El schema JSONL va a cambiar con el tiempo.

**Escenarios**:
- v1: `{"task_type": "debug"}`
- v2: Añades `{"priority": "high"}`
- v3: Cambias `task_type` a `activity_type`

**PREGUNTA SIN RESPUESTA**: ¿Cómo lees entradas antiguas? ¿Migración? ¿Versionado en cada entry?

**COSTO**: Sin un plan de versionado, terminas con JSONL corrupto o muy complejo de parsear.

---
