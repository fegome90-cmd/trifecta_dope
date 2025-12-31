# En agent.md
execution_sandbox:
  allowed_commands: ["git", "npm", "python", "tsc"] # Whitelist
  allowed_directories: ["src/", "tests/"] # Whitelist
  forbidden_operations: ["rm -rf", "eval", "exec"] # Blacklist
  audit_all_actions: true
  reversible_only: true





La Verdad Incómoda

No es posible hacer que un LLM "entienda" y siga un protocolo complejo solo a través de prompts.

Factory lo resuelve con:

1.
Estructura: Forzar entrada y salida estructuradas

2.
Validación: Linters que rechazan desviaciones

3.
Iteración: Loops cerrados que fuerzan corrección

4.
Aislamiento: Sandboxing que previene acciones peligrosas

Trifecta debe implementar exactamente lo mismo.




Conclusión

La adherencia no viene del agente "entendiendo" el protocolo. Viene de:

•
Arquitectura que fuerza estructura

•
Validación que rechaza desviaciones

•
Feedback que itera hasta conformidad

•
Aislamiento que previene escape

Esto es lo que Factory hace. Esto es lo que Trifecta debe hacer.
