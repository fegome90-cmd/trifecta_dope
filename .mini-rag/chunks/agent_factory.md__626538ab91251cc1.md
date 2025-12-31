- rule: "performance-metrics"
    id: "critical-path-metrics"
    severity: "info"
    description: "Las funciones críticas deben registrar métricas."
    target: "src/domain/use-cases/**/*.ts"
    require: "duration-metric"





10. Cómo el Agente Usa Este Documento

Cuando el agente recibe una tarea, sigue este protocolo:

1.
Lectura Inicial: Lee este archivo AGENTS.md completo.

2.
Análisis de Contexto: Identifica qué reglas son relevantes para la tarea.

3.
Generación de Código: Genera código que cumple con todas las reglas relevantes.

4.
Auto-Validación: Ejecuta el linter de Trifecta (que se genera a partir de este archivo).

5.
Iteración: Si hay violaciones, lee el feedback del linter y corrige el código.

6.
Justificación: Si debe desviarse de una regla, documenta la justificación.




11. Cambios y Evolución

Este documento es vivo. Cuando se descubren nuevos patrones o se necesitan nuevas reglas, se añaden aquí. El compilador de Trifecta detecta automáticamente los cambios y actualiza el linter.

Última actualización: 30 de diciembre de 2025 Versión: 1.0.0




El Esquema de AGENTS.md: La Constitución Ejecutable

Para: El Autor De: Editor Técnico Senior Fecha: 30 de diciembre de 2025

Filosofía Central: De la Intención Humana a la Validación Automática
