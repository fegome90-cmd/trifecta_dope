## 1. Límites Arquitectónicos (Architectural Boundaries)

Para mantener una arquitectura limpia, la capa de `core` nunca debe importar desde la capa de `api` o `ui`.

```yaml
- rule: "architectural-boundary"
  id: "core-isolation"
  severity: "error"
  description: "La capa 'core' no puede importar desde 'api' o 'ui'."
  target: "src/core/**/*.ts"
  disallow: 
    - "src/api/**/*.ts"
    - "src/ui/**/*.ts"


2. Convenciones de Código (Code Conventions)

Todas las funciones de servicio deben ser funciones puras y estar documentadas con TSDoc.

YAML


- rule: "function-style"
  id: "pure-services"
  severity: "warning"
  description: "Las funciones de servicio deben ser puras."
  target: "src/services/**/*.ts"
  enforce: "pure-function"

- rule: "documentation-coverage"
  id: "service-docs"
  severity: "info"
  description: "Las funciones de servicio deben tener TSDoc."
  target: "src/services/**/*.ts"
  minCoverage: 0.9


(Y así sucesivamente para otras categorías...)

Plain Text



### Tipos de Reglas y su Traducción a Linter

A continuación se detallan los tipos de reglas, su esquema YAML y cómo se compilan en reglas de linter reales (usando pseudocódigo de linter).

#### 1. `architectural-boundary`

*   **Propósito:** Hacer cumplir la separación de capas y módulos.
*   **Esquema YAML:**
    ```yaml
