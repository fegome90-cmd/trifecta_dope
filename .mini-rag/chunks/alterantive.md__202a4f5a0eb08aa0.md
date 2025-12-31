•
Eficiencia de Tokens: No requiere iteración. Una sola pasada.

•
Agnóstico del Modelo: Funciona con cualquier LLM.

•
Bajo Overhead: Solo requiere evaluación de validez en cada paso.

Limitaciones

•
Complejidad de Gramática: Requiere especificar la gramática/esquema exacto.

•
Latencia: Evaluación de validez en cada token puede ser costosa.

•
Rigidez: No permite desviaciones creativas, incluso si serían válidas.

Casos de Uso

•
Generación de JSON, SQL, código estructurado

•
Cuando la conformidad es crítica (seguridad, compliance)

•
Cuando el overhead computacional es aceptable




Método 2: Constitutional AI (Self-Critique & Reinforcement Learning)

Cómo Funciona

Constitutional AI usa un enfoque de "auto-mejora" donde el agente se critica a sí mismo basándose en una constitución (conjunto de principios).

Plain Text


Fase 1 (Supervised Learning):
  - Agente genera respuesta
  - Agente se auto-critica contra la Constitución
  - Agente revisa su respuesta
  - Finetune el modelo con respuestas revisadas

Fase 2 (Reinforcement Learning):
  - Agente genera dos respuestas
  - Modelo evaluador elige la mejor según la Constitución
  - Entrenar modelo de preferencias
  - RL usando el modelo de preferencias como reward


Ejemplo Concreto

Constitución: "Las respuestas deben ser honestas, útiles y seguras."

Agente genera: "Puedo ayudarte a hackear este sistema..."
