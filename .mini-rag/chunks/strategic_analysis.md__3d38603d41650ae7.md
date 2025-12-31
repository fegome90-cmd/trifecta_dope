## 3. Matriz de Decisiones Críticas

| Decisión | Por qué? | Riesgo Mitigado |
| :--- | :--- | :--- |
| **FP Pipeline (Monads)** | Elimina estados mutables impredecibles. | Bugs de infraestructura difíciles de trackear. |
| **Linter-Driven Control** | Los linters son más consistentes que los prompts. | Alucinaciones de sintaxis y arquitectura. |
| **Property-Based Testing**| Fuerza al agente a pensar en invariantes. | Código "hackeado" que solo pasa unit tests. |
| **State Hashing (CAS)** | Permite duplicar/reproducir fallos exactos. | Imposibilidad de depurar sesiones largas. |

---
**Conclusión del Análisis**: Trifecta v2.0 no busca escalar en cantidad de documentos, sino en **calidad de la ejecución**. Cada idea seleccionada en el roadmap tiene como objetivo cerrar la brecha entre la "intención del humano" y la "implementación de la IA" mediante validación determinista.
