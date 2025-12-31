- rule: "explicit-exports"
    id: "barrel-exports"
    severity: "info"
    description: "Los directorios deben tener un index.ts con exportaciones explícitas."
    target: "src/**/"
    require: "index.ts"





7. Patrones de Mimetismo (Mimicry Patterns)

7.1 Análisis de Patrones Existentes

Antes de escribir código nuevo, el agente debe analizar los patrones existentes en el proyecto.

YAML


  - rule: "mimicry-protocol"
    id: "pattern-analysis"
    severity: "warning"
    description: "El código nuevo debe seguir los patrones existentes."
    target: "src/**/*.ts"
    analyze:
      - "naming-patterns"
      - "function-signatures"
      - "error-handling"
      - "logging-patterns"
    tolerance: 0.85 # 85% de similitud con patrones existentes


7.2 Justificación de Desviaciones

Si el código se desvía de los patrones existentes, debe haber una justificación explícita.

YAML


  - rule: "deviation-justification"
    id: "explain-deviation"
    severity: "info"
    description: "Las desviaciones de patrones deben estar justificadas en comentarios."
    target: "src/**/*.ts"
    requireCommentWhen: "deviation-detected"
    commentPattern: "@deviation:"





8. Manejo de Errores (Error Handling)

8.1 Tipos de Error

MedLogger define tipos de error específicos para cada capa.

YAML
