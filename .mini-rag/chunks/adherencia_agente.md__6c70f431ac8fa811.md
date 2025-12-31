•
Restricciones de tokens que penalizan desviaciones

•
Validación de salida que rechaza respuestas que no siguen el formato

3. El Ciclo de Feedback Cerrado: Linter como Validador

Aquí es donde entra el linter. El linter no es solo una herramienta de validación; es el mecanismo de retroalimentación que fuerza la adherencia:

Plain Text


Usuario → Prompt Estructurado → Agente → Salida Estructurada → Linter → Feedback → Agente (Iteración)


Si el agente propone código que viola las reglas del linter:

•
El linter lo rechaza

•
Proporciona feedback específico

•
El agente recibe este feedback como entrada para el siguiente turno

•
El agente itera hasta pasar

Esto es crítico: El agente no puede simplemente ignorar el linter. El linter es parte del loop de ejecución, no un paso opcional.

4. AGENTS.md como Especificación Vinculante

Factory usa AGENTS.md (que es equivalente a tu AGENTS.md) como una especificación que el agente debe seguir. Pero no es solo documentación:

•
El agente lee AGENTS.md al inicio de cada sesión

•
El linter se genera automáticamente a partir de AGENTS.md

•
Las violaciones del linter son violaciones de AGENTS.md

•
El agente recibe feedback que referencia AGENTS.md específicamente

5. Sandboxing y Aislamiento: El Agente No Tiene Libertad

Factory implementa sandboxing estricto:

•
El agente solo puede ejecutar comandos whitelisteados
