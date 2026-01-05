### T7. Router/Gate de niveles: map → snippet → file

**Regla:** por defecto **NO leer archivo completo**. Solo si:

* no basta snippet, o
* hay ambigüedad que requiere más evidencia, o
* el usuario pide explícitamente.
  **DoD**
* El agente primero consulta skeleton → luego snippet.
* Lectura full file queda detrás de un gate explícito.
  **Tests**
* En tareas de navegación, bytes leídos deben bajar vs baseline.
* Gate: si intenta full file sin razón → FAIL.
  **Métrica**
* `bytes_read_per_task` ↓
* `accuracy_top1` >= baseline
* `fallback_rate` no sube más de X

---
