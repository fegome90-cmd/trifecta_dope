## 🔴 PROBLEMA #1: Impedance Mismatch

**Pregunta**: ¿Cómo agregas 50 eventos de telemetry en UNA entrada de session?

**Ejemplo real del JSONL**:
```
19:17:00 - lsp.spawn
19:17:00 - lsp.state_change
19:17:00 - lsp.daemon_status
19:17:00 - lsp.request (hover)
19:17:00 - lsp.request (hover)
19:17:03 - lsp.daemon_status
19:17:03 - lsp.request (hover)
```

¿Esto es UN task o SIETE? Telemetry no tiene concepto de "sesión de trabajo".

**NECESITARÍAS**:
- Agregar campo `session_id` a cada evento de telemetry
- Script que agrupe eventos por `session_id`
- Lógica para detectar cuándo termina una sesión

**COSTO**: Añades complejidad masiva al sistema de telemetry que NO necesita.

---
