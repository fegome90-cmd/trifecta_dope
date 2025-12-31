- rule: "naming-convention"
    id: "interface-prefix"
    severity: "warning"
    description: "Las interfaces deben empezar con 'I'."
    target: "src/**/*.ts"
    elementType: "interface"
    prefix: "I"

  - rule: "naming-convention"
    id: "class-pascal-case"
    severity: "warning"
    description: "Las clases deben usar PascalCase."
    target: "src/**/*.ts"
    elementType: "class"
    format: "PascalCase"

  - rule: "naming-convention"
    id: "variable-camel-case"
    severity: "info"
    description: "Las variables deben usar camelCase."
    target: "src/**/*.ts"
    elementType: "variable"
    format: "camelCase"


3.3 Documentación

Todas las funciones públicas en domain/ y api/ deben tener comentarios TSDoc.

YAML


  - rule: "documentation-coverage"
    id: "public-function-docs"
    severity: "warning"
    description: "Las funciones públicas deben tener TSDoc."
    target: "src/domain/**/*.ts"
    minCoverage: 0.95
    requireTSDoc: true





4. Seguridad y Privacidad (Security & Privacy)

4.1 Prohibiciones de Seguridad

Ciertas funciones y patrones están completamente prohibidos en el código de MedLogger.

YAML


  - rule: "security-guard"
    id: "no-eval"
    severity: "error"
    description: "El uso de 'eval' está prohibido."
    target: "src/**/*.ts"
    disallow: "eval"
