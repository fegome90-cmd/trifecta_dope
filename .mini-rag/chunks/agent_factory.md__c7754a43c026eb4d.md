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
