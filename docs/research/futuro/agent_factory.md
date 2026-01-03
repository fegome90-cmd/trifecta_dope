AGENTS.md - Ejemplo Completo: Proyecto "MedLogger"

Este documento define la Constitución del Agente para el proyecto MedLogger, una plataforma de logging médico. Todas las reglas aquí definidas son ejecutables y se hacen cumplir automáticamente a través del linter de Trifecta.




1. Visión y Principios

El proyecto MedLogger se construye sobre los siguientes principios:

•
Seguridad en Primer Lugar: Todos los datos de pacientes están protegidos por defecto.

•
Arquitectura Limpia: La lógica de negocio está completamente separada de la infraestructura.

•
Funciones Puras: La mayoría del código son funciones puras para facilitar el testing y la verificación.

•
Documentación Viva: El código es autodocumentado a través de tipos y comentarios.




2. Límites Arquitectónicos (Architectural Boundaries)

La arquitectura de MedLogger sigue el patrón de Arquitectura Limpia. Hay cuatro capas principales:

1.
core/: Lógica de negocio pura (sin dependencias externas)

2.
domain/: Entidades y casos de uso (depende de core/)

3.
infrastructure/: Acceso a datos, APIs externas (depende de domain/)

4.
api/: Controladores HTTP y puntos de entrada (depende de infrastructure/)

La regla fundamental es: cada capa solo puede importar de capas inferiores (más cercanas a core/).

YAML


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

AGENTS.md no es un simple archivo de documentación. Es una especificación declarativa y legible por humanos que se compila en reglas de linter ejecutables. Su propósito es cerrar la brecha entre la intención del arquitecto y la acción del agente.

El esquema se basa en una sintaxis de bloques de código YAML dentro de un archivo Markdown. El Markdown proporciona la explicación legible para humanos (el "porqué"), y el YAML proporciona la configuración estructurada para la máquina (el "cómo").

Estructura General de AGENTS.md

El archivo se organiza en secciones que corresponden a las categorías de control del agente. Cada sección contiene una explicación en Markdown seguida de uno o más bloques de código YAML que definen las reglas.

Markdown


# Constitución del Agente para el Proyecto "Phoenix"

Este documento define las reglas que gobiernan el comportamiento de los agentes de IA en este repositorio. El cumplimiento de estas reglas no es opcional.

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
    - rule: "architectural-boundary"
      id: string # ID único de la regla
      severity: "error" | "warning" | "info"
      description: string
      target: string # Glob pattern para los archivos a los que se aplica
      allow?: string[] # Opcional: Lista de globs de los que SÍ se puede importar
      disallow?: string[] # Opcional: Lista de globs de los que NO se puede importar
    ```
*   **Traducción a Linter (Pseudocódigo):**
    ```javascript
    // Compilador de AGENTS.md genera esto:
    createLinterRule("core-isolation", {
      meta: { docs: { description: "..." } },
      create: function(context) {
        return {
          ImportDeclaration(node) {
            const sourceFile = context.getFilename();
            if (micromatch.isMatch(sourceFile, "src/core/**/*.ts")) {
              const importPath = node.source.value;
              if (micromatch.isMatch(importPath, ["src/api/**/*.ts", "src/ui/**/*.ts"])) {
                context.report({ node, message: "Violación de límite arquitectónico." });
              }
            }
          }
        };
      }
    });
    ```

#### 2. `function-style`

*   **Propósito:** Hacer cumplir un estilo de codificación específico (puro, async, etc.).
*   **Esquema YAML:**
    ```yaml
    - rule: "function-style"
      id: string
      severity: "error" | "warning" | "info"
      description: string
      target: string
      enforce: "pure-function" | "async-only" | "no-classes"
    ```
*   **Traducción a Linter (Pseudocódigo):**
    ```javascript
    // Compilador de AGENTS.md genera esto para "pure-function":
    createLinterRule("pure-services", {
      // ...
      create: function(context) {
        return {
          FunctionDeclaration(node) {
            // Analiza el AST de la función para detectar efectos secundarios
            // (ej. acceso a variables globales, I/O, mutación de argumentos)
            if (hasSideEffects(node.body)) {
              context.report({ node, message: "La función debe ser pura." });
            }
          }
        };
      }
    });
    ```

#### 3. `naming-convention`

*   **Propósito:** Estandarizar la nomenclatura de variables, funciones, clases, etc.
*   **Esquema YAML:**
    ```yaml
    - rule: "naming-convention"
      id: string
      severity: "error" | "warning" | "info"
      description: string
      target: string
      elementType: "variable" | "function" | "class" | "interface"
      format: "camelCase" | "PascalCase" | "snake_case"
      prefix?: string
      suffix?: string
    ```
*   **Traducción a Linter (Pseudocódigo):**
    ```javascript
    // Compilador de AGENTS.md genera esto:
    createLinterRule("interface-naming", {
      // ...
      create: function(context) {
        return {
          TSInterfaceDeclaration(node) {
            const interfaceName = node.id.name;
            if (!/^I[A-Z]/.test(interfaceName)) { // Ejemplo para prefijo "I"
              context.report({ node, message: "Las interfaces deben empezar con 'I'." });
            }
          }
        };
      }
    });
    ```

#### 4. `security-guard`

*   **Propósito:** Prevenir vulnerabilidades de seguridad comunes.
*   **Esquema YAML:**
    ```yaml
    - rule: "security-guard"
      id: string
      severity: "error"
      description: string
      target: string
      disallow: "eval" | "dangerouslySetInnerHTML" | "process-env"
    ```
*   **Traducción a Linter (Pseudocódigo):**
    ```javascript
    // Compilador de AGENTS.md genera esto para "eval":
    createLinterRule("no-eval", {
      // ...
      create: function(context) {
        return {
          CallExpression(node) {
            if (node.callee.name === 'eval') {
              context.report({ node, message: "El uso de 'eval' está prohibido." });
            }
          }
        };
      }
    });
    ```

### El Compilador de `AGENTS.md`

El corazón del sistema es un "compilador" que realiza los siguientes pasos:

1.  **Parseo:** Lee `AGENTS.md` y extrae los bloques de código YAML.
2.  **Validación:** Valida cada bloque YAML contra el esquema de reglas definido.
3.  **Generación de Código:** Para cada regla validada, genera el código de la regla de linter correspondiente utilizando plantillas predefinidas.
4.  **Configuración del Linter:** Escribe la configuración final del linter (ej. `.eslintrc.js`) que importa y habilita las reglas generadas.

Este compilador se ejecuta como parte del comando `trifecta ctx build`, asegurando que el entorno del agente siempre esté sincronizado con la "Constitución" del proyecto.

### Conclusión

Este esquema transforma `AGENTS.md` de un documento pasivo a un artefacto de ingeniería activo. Proporciona un lenguaje común y estructurado para que los humanos definan la intención y las máquinas la hagan cumplir, permitiendo que los agentes de IA operen con un nivel de autonomía, seguridad y predictibilidad sin precedentes.


Este documento es excelente. Has definido un **DSL (Domain Specific Language)** embebido en Markdown que actúa como puente entre la semántica humana y la sintaxis de máquina. Es básicamente un "Contrato Inteligente" para el desarrollo de software.

Como "Editor Técnico", tengo una observación crítica para la implementación en **Trifecta**:

**No escribas un linter desde cero.**
En tu sección de "Traducción a Linter", sugieres generar código JavaScript (`createLinterRule...`). Esto es costoso de mantener y frágil.
**La Alternativa Pragmática:** Escribe un **Transpilador** que convierta tu esquema YAML simplificado directamente a configuraciones de **`ast-grep` (sg)** y **`ruff`**.

Aquí tienes la implementación del **Compilador Trifecta** en Python. Este script lee `AGENTS.md` y escupe un `sgconfig.yml` listo para usar.

### 1. El Compilador (`src/trifecta/compiler.py`)

Este script implementa la lógica de extracción y traducción.

```python
import re
import yaml
import sys
from pathlib import Path

# Esquema de traducción: Tu Regla -> ast-grep Rule
def compile_boundary_rule(rule):
    """
    Convierte 'architectural-boundary' a regla de ast-grep
    """
    # Lógica: Si estoy en 'target', NO puedo tener 'import' de 'disallow'
    disallowed_patterns = "|".join([p.replace("**/*.ts", "") for p in rule.get('disallow', [])])

    return {
        'id': rule['id'],
        'message': rule['description'],
        'severity': rule['severity'],
        'language': 'TypeScript',
        'rule': {
            'pattern': 'import $IMPORTS from "$SOURCE"',
            'all': [
                {
                    'inside': {
                        'subdir': rule['target'].replace('**/*.ts', '')
                    }
                },
                {
                    'has': {
                        'field': 'source',
                        'regex': disallowed_patterns
                    }
                }
            ]
        }
    }

def compile_security_rule(rule):
    """
    Convierte 'security-guard' a regla de ast-grep
    """
    pattern_map = {
        'eval': 'eval($$$ARGS)',
        'dangerouslySetInnerHTML': 'dangerouslySetInnerHTML={$$$PROPS}',
        'process-env': 'process.env.$VAR'
    }

    return {
        'id': rule['id'],
        'message': rule['description'],
        'severity': rule['severity'],
        'language': 'TypeScript',
        'rule': {
            'pattern': pattern_map.get(rule['disallow'], rule.get('pattern', 'TODO'))
        }
    }

def parse_agents_md(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Regex para extraer bloques YAML
    # Busca ```yaml ... ```
    yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)

    compiled_rules = []

    for block in yaml_blocks:
        try:
            rules_list = yaml.safe_load(block)
            if not isinstance(rules_list, list): continue # Ignorar configs que no son listas de reglas

            for rule in rules_list:
                if rule['rule'] == 'architectural-boundary':
                    compiled_rules.append(compile_boundary_rule(rule))
                elif rule['rule'] == 'security-guard':
                    compiled_rules.append(compile_security_rule(rule))
                # Aquí añadirías 'naming-convention' y 'function-style'

        except yaml.YAMLError as e:
            print(f"Error parseando bloque YAML: {e}")

    return {'rules': compiled_rules}

if __name__ == "__main__":
    # Uso: python compiler.py AGENTS.md > sgconfig.yml
    input_file = "AGENTS.md"
    result = parse_agents_md(input_file)
    print(yaml.dump(result, sort_keys=False))

```

### 2. El Resultado Compilado (`sgconfig.yml`)

Si ejecutas el script anterior sobre tu `AGENTS.md`, obtienes esto automáticamente. Esto es lo que `ast-grep` consume:

```yaml
rules:
  - id: core-isolation
    message: La capa 'core' no puede importar desde 'api' o 'ui'.
    severity: error
    language: TypeScript
    rule:
      pattern: import $IMPORTS from "$SOURCE"
      all:
        - inside:
            subdir: src/core/
        - has:
            field: source
            regex: src/api/|src/ui/

  - id: no-eval
    message: El uso de 'eval' está prohibido.
    severity: error
    language: TypeScript
    rule:
      pattern: eval($$$ARGS)

```

### 3. Integración en el Flujo de Trabajo

Ahora el comando `trifecta ctx build` hace dos cosas:

1. **Para el LLM (Contexto):** Lee el `AGENTS.md` y se lo inyecta como texto plano en el System Prompt.
* *Efecto:* El agente "sabe" las reglas y trata de seguirlas.


2. **Para la Máquina (Validación):** Ejecuta el compilador (`compiler.py`), genera `sgconfig.yml` temporal y corre el scan.
* *Efecto:* Si el agente "olvidó" una regla, la máquina lo atrapa.



### Reto Técnico: La regla `function-style` (Puros vs Impuros)

Esta es la más difícil de transpilar a un linter estático simple (`ast-grep`).

* **Tu definición:** "Las funciones deben ser puras".
* **El problema:** Detectar impureza estáticamente es difícil.
* **La solución aproximada (Heurística):**
En lugar de detectar "pureza", detectamos "impureza obvia".
*Traducción del compilador para `pure-function`:*
```yaml
- id: pure-services
  message: Función impura detectada en servicio. Evita I/O, random o estado global.
  severity: warning
  rule:
    any:
      - pattern: Math.random()
      - pattern: Date.now()
      - pattern: console.log($$$)
      - pattern: fs.readFile($$$)
      - pattern: fetch($$$)
  inside:
    subdir: src/services

```



### Conclusión del Editor Técnico

Tu propuesta de `AGENTS.md` es viable y muy potente.
El cambio clave es **no inventar tu propio motor de linting**. Usa `AGENTS.md` como una **Interfaz de Alto Nivel** que orquesta herramientas de bajo nivel (`ast-grep`, `ruff`, `biome`) que ya están optimizadas en Rust.

**Siguiente paso sugerido:**
¿Implementamos la regla `naming-convention` en el compilador Python? Es un excelente caso de uso para expresiones regulares dentro de `ast-grep`.
