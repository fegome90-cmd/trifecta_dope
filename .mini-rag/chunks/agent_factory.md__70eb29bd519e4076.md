La cobertura de tests debe ser al menos del 80% en core/ y domain/.

YAML


  - rule: "coverage-threshold"
    id: "core-coverage"
    severity: "warning"
    description: "La cobertura de 'core/' debe ser >= 80%."
    target: "src/core/**/*.ts"
    minCoverage: 0.80

  - rule: "coverage-threshold"
    id: "domain-coverage"
    severity: "warning"
    description: "La cobertura de 'domain/' debe ser >= 80%."
    target: "src/domain/**/*.ts"
    minCoverage: 0.80





6. Buscabilidad (Searchability & Grep-ability)

6.1 Estructura de Archivos

La estructura de archivos debe ser predecible y fácil de navegar.

YAML


  - rule: "file-structure"
    id: "predictable-layout"
    severity: "warning"
    description: "La estructura de archivos debe seguir el patrón definido."
    target: "src/**/*.ts"
    structure:
      "src/core/":
        - "entities/"
        - "value-objects/"
        - "services/"
      "src/domain/":
        - "use-cases/"
        - "repositories/"
        - "errors/"
      "src/infrastructure/":
        - "database/"
        - "external-apis/"
        - "repositories/"
      "src/api/":
        - "controllers/"
        - "middleware/"
        - "routes/"


6.2 Exportaciones Explícitas

Los módulos deben exportar explícitamente lo que es público.

YAML
