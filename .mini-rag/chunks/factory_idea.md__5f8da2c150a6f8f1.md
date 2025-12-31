### Comparativa: Tu flujo actual vs. Flujo Factory/Trifecta

| Fase | Tu flujo actual (Probable) | Flujo Factory/Trifecta |
| --- | --- | --- |
| **Instrucción** | "Crea un login seguro en Python" | Lee `AGENTS.md` + Prompt Usuario |
| **Generación** | El modelo escribe código de una vez | El modelo escribe, guarda en `/tmp` |
| **Validación** | Tú lees el código y buscas errores | El script ejecuta `ruff` y `ast-grep` |
| **Corrección** | Tú le dices: "Te faltó el tipo de retorno" | El linter le dice: `MissingReturnType` |
| **Entrega** | Copias y pegas código con bugs potenciales | Recibes código que ya compila y pasa reglas |
