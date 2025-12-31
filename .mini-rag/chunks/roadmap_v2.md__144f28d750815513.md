### Fase 1: El Núcleo Indestructible (Q1)

*Foco: Establecer la base de fiabilidad y estructura.*

1. **Refuerzo del North Star**: Automatizar la validación de que cada segmento tiene sus 3+1 archivos esenciales con el formato correcto.
2. **Linter-Driven Loop**: Modificar el orquestador para que el agente reciba errores de `ruff` y `ast-grep` como instrucciones de corrección prioritarias antes de reportar éxito.
3. **AGENTS.md (MVP)**: Implementar el primer compilador que lea reglas YAML simples y las aplique vía `ast-grep`.
