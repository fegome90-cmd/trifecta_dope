# Strategic Roadmap: Trifecta v2.0

Este roadmap prioriza las implementaciones según el **Priority Score (PS)**, calculado como el producto de la **Utilidad del Producto (1-10)** y el **ROI Individual (%)**. El objetivo es ejecutar primero lo que genera mayor valor real con el menor esfuerzo/riesgo técnico.

## Cuadro de Priorización (Rankeado)

| Prioridad | Implementación | Área | Utilidad | ROI | Score (PS) |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **🥇 1** | **Strict North Star (3+1 files)** | Core | 10 | 100% | **100** |
| **🥈 2** | **Linter-Driven Loop (API Control)** | Quality | 9 | 95% | **85.5** |
| **🥉 3** | **Constitution (AGENTS.md) Ph1** | Quality | 9 | 90% | **81.0** |
| **🥉 3** | **Property-Based Testing** | Quality | 9 | 90% | **81.0** |
| **4** | **Progressive Disclosure** | Context | 8 | 95% | **76.0** |
| **5** | **SHA-256 Lock (TOFU Security)** | Resilience| 8 | 90% | **72.0** |
| **6** | **Time Travel Debugging (CAS)** | Obs. | 7 | 95% | **66.5** |
| **7** | **AST/LSP For Hot Files** | Context | 8 | 80% | **64.0** |

---

## Fases de Implementación

### Fase 1: El Núcleo Indestructible (Q1)

*Foco: Establecer la base de fiabilidad y estructura.*

1. **Refuerzo del North Star**: Automatizar la validación de que cada segmento tiene sus 3+1 archivos esenciales con el formato correcto.
2. **Linter-Driven Loop**: Modificar el orquestador para que el agente reciba errores de `ruff` y `ast-grep` como instrucciones de corrección prioritarias antes de reportar éxito.
3. **AGENTS.md (MVP)**: Implementar el primer compilador que lea reglas YAML simples y las aplique vía `ast-grep`.

### Fase 2: Inteligencia y Economía (Q2)

*Foco: Reducción de costos y aumento de precisión lógica.*

1. **Progressive Disclosure (Search/Get)**: Implementar la recuperación bajo demanda para evitar enviar archivos completos innecesariamente.
2. **Property-Based Testing**: Integrar `hypothesis` para que el agente pruebe invariantes lógicas, elevando el nivel de los tests unitarios.
3. **SHA-256 Security**: Asegurar la integridad de la librería de skills local con el sistema de lockfiles.

### Fase 3: Resiliencia Avanzada (Q3)

*Foco: Depuración quirúrgica y seguridad de flujo.*

1. **Time Travel Debugging**: Implementar el hashing de estados para permitir reproducir exactamente cualquier momento de la sesión del agente.
2. **AST/LSP Integration**: Cambiar la búsqueda de texto por búsqueda de símbolos reales del código.
3. **Judge of Coherence**: Añadir un "Juez" (modelo ligero) que valide que el código entrega lo prometido en el plan.

---

## Métricas de Éxito del Roadmap

* **Fiabilidad**: Reducción del 80% en errores de sintaxis reportados al usuario.
* **Economía**: Reducción del 50% en el consumo de tokens por búsqueda de contexto.
* **Debuggability**: Tiempo de reproducción de errores reducido a <1 minuto vía Time Travel.
