### Arquitectura Trifecta v2.0 (Endurecida)

El diagrama de flujo ahora incluye estos guardianes dinámicos:

1. **Input:** Tarea del Usuario.
2. **JIT Constitution:** Trifecta selecciona las reglas relevantes.
3. **Generación:** Agente genera Plan + Código + **Tests de Propiedad**.
4. **Juez de Coherencia:** ¿El código cumple el plan? (Si no -> Feedback).
5. **Análisis de Flujo (Taint):** ¿Hay datos sucios tocando sumideros? (Si sí -> Feedback).
6. **Linter Estático:** `ruff` / `ast-grep`.
7. **Test Dinámico (Fuzzing):** `hypothesis` bombardea el código con 100 inputs.
8. **Compresión:** Si el loop continúa, se resume el estado anterior.
9. **Éxito.**

**Veredicto Final:**
Has movido la arquitectura de "Correcta Teóricamente" a **"Resiliente en Práctica"**. Ahora no solo buscas código limpio, buscas código que sobreviva al contacto con la realidad y la malicia.

¿Por dónde empezamos? La **Compresión de Estado (Punto 3)** es crítica si planeas tareas largas. El **Property-Based Testing (Punto 1)** es crítico si planeas escribir lógica de negocio real.
