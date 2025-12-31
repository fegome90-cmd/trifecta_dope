### 🛡️ Por qué esto cumple tus requisitos

| Requisito | Implementación |
| --- | --- |
| **Lockfile Obligatorio** | Si no hay lockfile o no coincide el hash, el build falla. |
| **Read Only** | El builder nunca toca los archivos fuente, solo lee y verifica. |
| **Allowlist** | Solo se procesan las entradas explícitas en `trifecta.yaml`. |
| **Update Explícito** | Los cambios en la librería no se propagan solos. Requieren intervención humana (`ctx update`). |
| **Reportes** | El `ctx update` genera un diff de seguridad antes de aceptar. |
