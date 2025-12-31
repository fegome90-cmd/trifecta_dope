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
