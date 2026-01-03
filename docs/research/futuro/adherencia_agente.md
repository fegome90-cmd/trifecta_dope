Cómo Factory Fuerza la Adherencia al Protocolo del Agente

Hallazgos Clave de la Investigación

Después de revisar la documentación de Factory, he identificado el mecanismo real de cómo Factory hace que los agentes adhieran a protocolos y métodos. No es mágico, es arquitectónico.

El Mecanismo Central: Structured Communication Protocol

Factory no confía en que el agente "entienda" las instrucciones. En su lugar, implementa un protocolo estructurado de comunicación que es bidireccional y validado.

1. Entrada Estructurada: El Prompt Sigue un Patrón

El usuario no escribe un prompt libre. Factory guía al usuario a través de un patrón específico:

Plain Text


[GOAL]: Estado claro del objetivo
[CONTEXT]: Información relevante (archivos, errores, enlaces)
[APPROACH]: Cómo verificar que está hecho
[CONSTRAINTS]: Límites (qué NO hacer)


Esto no es sugerencia; es el formato que Factory espera. El agente está entrenado para esperar esta estructura.

2. Salida Estructurada: El Agente Responde en Formato Definido

El agente no puede simplemente escribir código y decir "listo". Debe responder en un formato específico:

Plain Text


[PLAN]: Qué va a hacer (paso a paso)
[IMPLEMENTATION]: El código/cambios
[VALIDATION]: Cómo se verifica que funciona
[RISKS]: Qué podría salir mal


Esta estructura es forzada por el modelo mismo a través de:

•
Fine-tuning específico para este patrón

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

•
El agente solo puede escribir en directorios específicos

•
El agente no puede acceder a secretos o datos sensibles sin aprobación

•
Todas las acciones son auditadas y reversibles

Esto significa que incluso si el agente quisiera desviarse, no podría.

6. Specification Mode: Planificación Forzada

Para tareas complejas, Factory fuerza un modo de "planificación":

1.
El agente primero crea un plan detallado

2.
El usuario lo revisa y aprueba

3.
Solo entonces el agente implementa

Esto previene que el agente tome decisiones arquitectónicas sin supervisión.




Cómo Esto Se Traduce a Trifecta

El mecanismo de Factory es agnóstico del modelo. Funciona porque:

1.
Estructura de Entrada: El usuario proporciona contexto estructurado

2.
Estructura de Salida: El agente responde en formato definido

3.
Validación Automática: El linter valida cada paso

4.
Iteración Controlada: El agente itera basándose en feedback del linter

5.
Aislamiento: El agente no tiene libertad para desviarse

Implementación en Trifecta

Para que Trifecta implemente esto, necesita:

A. Protocolo de Entrada Estructurada

YAML


# En trifecta.yaml o como parte de prime.md
input_protocol:
  required_fields:
    - goal: "El objetivo de la tarea"
    - context: "Información relevante"
    - approach: "Cómo verificar"
    - constraints: "Qué NO hacer"
  validation: "strict" # Rechazar si faltan campos


B. Protocolo de Salida Estructurada

El agente debe responder siempre en este formato:

YAML


output_protocol:
  required_sections:
    - plan: "Qué va a hacer"
    - implementation: "El código/cambios"
    - validation: "Cómo se verifica"
    - risks: "Qué podría salir mal"
  validation: "strict" # Rechazar si faltan secciones


C. El Compilador de AGENTS.md a Linter

El compilador debe:

1.
Parsear AGENTS.md

2.
Generar reglas de linter

3.
Integrar estas reglas en el loop de ejecución del agente

4.
Proporcionar feedback que referencia AGENTS.md específicamente

D. El Loop de Iteración Forzada

Plain Text


Agente propone acción → Linter valida →
  Si pasa: Ejecutar
  Si falla: Proporcionar feedback → Agente itera


El agente no puede salir de este loop hasta que pase todas las validaciones.

E. Sandboxing y Aislamiento

YAML


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
