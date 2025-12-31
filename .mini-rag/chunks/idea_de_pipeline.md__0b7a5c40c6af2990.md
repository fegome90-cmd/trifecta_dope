### 3.2 El Motor de Observabilidad ("Flight Recorder")

En lugar de logs de texto plano, el pipeline emite una **Traza de Eventos Estructurados** (JSONL).
Cada evento es una tupla: `(Timestamp, EventType, Payload, StateHash, Metrics)`.

* **Traceability:** Podemos reconstruir la sesión completa.
* **Meta-Debugging:** Vinculación directa entre un error de ejecución y la regla específica de `AGENTS.md` que se violó. El log no dice "Error", dice "Violación de Regla #3: Arquitectura Limpia".
