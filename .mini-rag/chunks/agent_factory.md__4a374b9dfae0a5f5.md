- rule: "error-handling"
    id: "layer-specific-errors"
    severity: "warning"
    description: "Cada capa debe usar sus tipos de error específicos."
    target: "src/**/*.ts"
    errorTypes:
      "src/core/": ["CoreError"]
      "src/domain/": ["DomainError", "ValidationError"]
      "src/infrastructure/": ["DatabaseError", "ExternalAPIError"]
      "src/api/": ["HTTPError", "AuthenticationError"]


8.2 Logging de Errores

Todos los errores deben ser registrados con contexto.

YAML


  - rule: "error-logging"
    id: "contextual-logging"
    severity: "warning"
    description: "Los errores deben ser registrados con contexto."
    target: "src/**/*.ts"
    require: "structured-logging"
    fields: ["timestamp", "level", "message", "context", "stack"]





9. Observabilidad (Observability)

9.1 Logging Estructurado

Todos los logs deben ser estructurados con campos consistentes.

YAML


  - rule: "structured-logging"
    id: "log-format"
    severity: "info"
    description: "Los logs deben usar el formato estructurado definido."
    target: "src/**/*.ts"
    format: "json"
    requiredFields: ["timestamp", "level", "service", "message"]


9.2 Métricas

Las funciones críticas deben registrar métricas de rendimiento.

YAML
