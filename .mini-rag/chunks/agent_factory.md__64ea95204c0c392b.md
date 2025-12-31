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
