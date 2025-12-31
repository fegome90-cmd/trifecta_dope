### 3.3 El Sistema de Métricas (Telemetría MDP)

Tratamos al agente como un Proceso de Decisión de Markov .

* **Fricción de Validación:** ¿Cuántos intentos necesita el agente para pasar el linter? (Métrica de calidad del Prompt).
* **Recompensa ():** Asignación automática de puntos (+10 Test Pass, -5 Linter Fail). Permite evaluar objetivamente si una nueva versión del modelo es "mejor" o "peor".
* **Entropía:** Medición de la "confianza" del modelo en sus decisiones.
