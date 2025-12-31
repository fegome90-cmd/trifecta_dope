6.
Agente reporta: Explica qué hizo y por qué

4. Diferencias Clave vs. RAG/Prompt Engineering Tradicional

Aspecto
Tradicional
Factory
Control
Prompts largos y ambiguos
Linters + AGENTS.md (ejecutables)
Validación
Manual o tests posteriores
Automática en cada paso
Escalabilidad
Degradación con complejidad
Mejora con reglas claras
Predictibilidad
Emergente e impredecible
Determinista y verificable
Feedback Loop
Lento (humano)
Rápido (automático)




5. La Innovación Central: Linters como API de Control

Factory ha invertido el paradigma. En lugar de:

•
Intentar que el agente "entienda" el código existente (costoso en tokens)

•
Escribir prompts cada vez más complejos

Factory hace:

•
Define reglas explícitas en linters

•
El agente recibe feedback automático e inmediato

•
El agente se auto-corrige iterativamente

•
"Lint passing" se convierte en la definición de "Done"

Implicaciones para Trifecta-Git

1.
AGENTS.md es más poderoso que skill.md: Factory no solo proporciona instrucciones, sino que las convierte en reglas ejecutables.

2.
Linters son el verdadero control: No es suficiente decirle al agente qué hacer; necesitas validación automática.

3.
El ciclo de retroalimentación es crítico: El agente debe poder iterar rápidamente basándose en feedback automático.

4.
La explainabilidad es arquitectónica: No es un agregado, sino un componente central.
