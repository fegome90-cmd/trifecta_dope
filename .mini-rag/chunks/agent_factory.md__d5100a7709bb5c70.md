- rule: "security-guard"
    id: "no-hardcoded-secrets"
    severity: "error"
    description: "Los secretos no deben estar hardcodeados."
    target: "src/**/*.ts"
    disallow: "hardcoded-secrets"
    pattern: "/(password|secret|api_key|token)\\s*=\\s*['\"].*['\"]/i"

  - rule: "security-guard"
    id: "no-console-logs"
    severity: "warning"
    description: "No se deben usar console.log en producción. Usar logger."
    target: "src/**/*.ts"
    disallow: "console-log"


4.2 Validación de Entrada

Todas las funciones que aceptan entrada del usuario deben validar sus parámetros.

YAML


  - rule: "input-validation"
    id: "api-endpoint-validation"
    severity: "error"
    description: "Los endpoints de API deben validar todas las entradas."
    target: "src/api/controllers/**/*.ts"
    require: "schema-validation"
    tool: "zod" # O "joi", "yup", etc.





5. Testabilidad (Testability & Coverage)

5.1 Colocación de Tests

Los archivos de test deben estar colocados junto al código que prueban, con la extensión .test.ts.

YAML


  - rule: "test-colocalization"
    id: "colocated-tests"
    severity: "warning"
    description: "Los tests deben estar colocados junto al código."
    target: "src/**/*.ts"
    exclude: "src/**/*.test.ts"
    requireTest: true
    testPattern: "{file}.test.ts"


5.2 Cobertura de Tests
