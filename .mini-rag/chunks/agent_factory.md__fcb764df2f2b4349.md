rules:
  - rule: "architectural-boundary"
    id: "layer-isolation"
    severity: "error"
    description: "Cada capa solo puede importar de capas inferiores."
    boundaries:
      - layer: "api"
        canImportFrom: ["infrastructure", "domain", "core"]
      - layer: "infrastructure"
        canImportFrom: ["domain", "core"]
      - layer: "domain"
        canImportFrom: ["core"]
      - layer: "core"
        canImportFrom: []


Ejemplos de Violaciones Detectadas

•
❌ src/core/patient.ts importa desde src/api/routes.ts → ERROR

•
❌ src/domain/use-cases/login.ts importa desde src/infrastructure/db.ts → ERROR (debería inyectarse)

•
✅ src/api/controllers/patient.ts importa desde src/domain/use-cases/get-patient.ts → OK




3. Convenciones de Código (Code Conventions)

3.1 Estilo de Funciones

Las funciones en core/ y domain/ deben ser funciones puras. Las funciones en infrastructure/ pueden tener efectos secundarios, pero deben estar claramente documentadas.

YAML


  - rule: "function-style"
    id: "pure-core-functions"
    severity: "error"
    description: "Las funciones en 'core/' deben ser puras."
    target: "src/core/**/*.ts"
    enforce: "pure-function"
    allowedSideEffects: []


3.2 Convenciones de Nomenclatura

Las interfaces deben empezar con I, las clases con mayúscula, las variables con camelCase.

YAML
