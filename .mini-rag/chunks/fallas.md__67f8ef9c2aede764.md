### 4. Contra el Flujo Tóxico: **Taint Analysis Estático (Heurístico)**

*El problema:* `ast-grep` no ve que `user_input` llega a `subprocess.call`.

**Solución Técnica:** **Marcado de Fuentes y Sumideros (Sources & Sinks).**
Usamos una configuración avanzada de `ast-grep` o `CodeQL` (si quieres ser hardcore) para rastrear flujo.

* **Regla:** Definimos "Variables Sucias" (todo lo que venga de `sys.argv`, `input()`, `requests.get`).
* **Regla:** Definimos "Sumideros Peligrosos" (`eval`, `exec`, `subprocess`, `open(..., 'w')`).
* **Validación:** El linter falla si hay un camino directo entre Sucio y Peligroso sin pasar por una función de limpieza (`sanitize_path`, `validate_input`).
* **Implementación:** En Trifecta, obligamos al uso de *Wrappers Seguros* (`SafeIO.write`) y prohibimos las nativas (`open`).
