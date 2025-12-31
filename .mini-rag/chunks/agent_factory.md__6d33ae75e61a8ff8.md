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
