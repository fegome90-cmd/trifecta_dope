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
