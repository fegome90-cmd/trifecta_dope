Tres Métodos Alternativos Probados para Forzar Adherencia en Agentes IA

Introducción

Después de investigar en profundidad, he identificado tres métodos alternativos a Factory que son igualmente robustos y probados en producción. Cada uno tiene ventajas y limitaciones distintas.




Método 1: Constrained Decoding (Token Masking)

Cómo Funciona

Constrained Decoding modifica el proceso de generación del modelo en tiempo real, no después. En lugar de permitir que el modelo elija libremente entre 50,000 tokens, se restringe a tokens válidos en cada paso.

Plain Text


Paso 1: Modelo genera distribución de probabilidad sobre todos los tokens
Paso 2: Evaluador determina qué tokens son válidos (según gramática/esquema)
Paso 3: Token masking: Se ponen a cero los tokens inválidos
Paso 4: Renormalizar y samplear de los tokens válidos


Ejemplo Concreto

Generando JSON, después de {"name": "Alice", solo son válidos:

•
, (para agregar otro campo)

•
} (para cerrar)

El modelo podría asignar probabilidad a a, b, {, etc., pero el masking los elimina antes de samplear.

Fórmula Matemática

Plain Text


p_constrained(t) = p_original(t) / Σ(p_original(t') para t' válido)


Esto preserva las preferencias del modelo pero garantiza conformidad.

Ventajas

•
Garantía Matemática: 100% de conformidad. Es imposible generar output inválido.

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

Auto-crítica: "Esto viola el principio de seguridad. Debería rechazar."

Revisión: "No puedo ayudarte con eso, pero puedo..."

Ventajas

•
Adaptabilidad: La Constitución puede cambiar sin reentrenamiento.

•
Escalabilidad: Usa AI feedback, no requiere etiquetado humano masivo.

•
Interpretabilidad: La Constitución es legible y auditable.

•
Robustez: Aprende a manejar edge cases a través de RL.

Limitaciones

•
Costo Computacional: Requiere dos fases de entrenamiento.

•
Complejidad: Necesita definir una Constitución clara y completa.

•
Latencia en Inferencia: No es más rápido que generación normal.

•
Sesgo de Constitución: Si la Constitución es sesgada, el modelo lo será.

Casos de Uso

•
Alineamiento de valores (seguridad, ética)

•
Cuando la conformidad es importante pero no crítica

•
Sistemas que necesitan adaptarse a nuevos principios




Método 3: Formal Verification + ReAct (Reasoning Traces + Model Checking)

Cómo Funciona

Formal Verification convierte planes en lenguaje natural a modelos formales (Kripke structures) y especificaciones en Temporal Logic (LTL), luego usa model checking para verificar que el plan cumple con las propiedades deseadas.

Plain Text


Paso 1: Agente genera plan en lenguaje natural
Paso 2: LLM traduce plan a Kripke structure (máquina de estados)
Paso 3: LLM especifica propiedades deseadas en LTL
Paso 4: Model checker (ej. NuSMV) verifica si plan cumple propiedades
Paso 5: Si falla, feedback al agente para revisar


Ejemplo Concreto

Plan Natural: "Primero compilar, luego ejecutar tests, luego deployar"

Kripke Structure:

Plain Text


States: {compile, tests, deploy, error}
Initial: compile
Transitions: compile → tests → deploy
            compile → error (si falla)


LTL Properties:

Plain Text


G(compile_done → F(tests_done))  // Siempre que compile, eventualmente tests
G(error → ¬deploy)               // Si hay error, nunca deployar
F(deploy_done)                   // Eventualmente deployar


Model Checker: Verifica que todas las propiedades se cumplen.

Ventajas

•
Garantía Formal: Prueba matemática de que el plan es correcto.

•
Detecta Deadlocks: Identifica situaciones donde el agente se queda atrapado.

•
Explainabilidad: Las propiedades LTL son legibles.

•
Completitud: Verifica todos los caminos posibles, no solo los probables.

Limitaciones

•
Complejidad Expresiva: LTL es difícil de escribir para no expertos.

•
Escalabilidad: Model checking puede ser exponencial en el tamaño del estado.

•
Overhead: Requiere traducción a formal y verificación.

•
Rigidez: No maneja incertidumbre bien.

Casos de Uso

•
Sistemas críticos (aviación, medicina, defensa)

•
Cuando necesitas garantías matemáticas

•
Planes complejos con muchas interdependencias




Comparativa de los Tres Métodos

Aspecto
Constrained Decoding
Constitutional AI
Formal Verification
Garantía de Conformidad
100% (matemática)
~95% (empírica)
100% (formal)
Velocidad de Inferencia
Lenta (overhead por token)
Normal
Normal + verificación
Complejidad de Setup
Media (gramática)
Alta (Constitución)
Muy Alta (LTL)
Adaptabilidad
Baja (requiere cambiar gramática)
Alta (cambiar Constitución)
Media (cambiar LTL)
Interpretabilidad
Baja (tokens)
Alta (Constitución)
Alta (LTL)
Escalabilidad
Media
Alta
Baja (exponencial)
Costo Computacional
Medio (por token)
Alto (dos fases)
Alto (model checking)
Casos de Uso
Estructurado (JSON, SQL)
Valores/ética
Crítico/formal







Recomendación para Trifecta

Híbrido de los tres métodos:

1.
Para Estructura (Output): Usar Constrained Decoding para garantizar que el output sigue el formato esperado (Plan, Implementation, Validation, Risks).

2.
Para Comportamiento (Agente): Usar Constitutional AI con una Constitución derivada de AGENTS.md para que el agente se auto-critique y mejore.

3.
Para Planes Críticos: Usar Formal Verification para planes complejos que afecten infraestructura crítica.

Arquitectura Propuesta

Plain Text


Entrada Estructurada
    ↓
Agente Lee AGENTS.md (Constitución)
    ↓
Agente Genera Plan (ReAct)
    ↓
Constrained Decoding (garantiza formato)
    ↓
Formal Verification (si es crítico)
    ↓
Constitutional AI Feedback (auto-crítica)
    ↓
Si pasa todo: Ejecutar
Si falla: Iterar





Conclusión

No existe un único método perfecto. Factory usa una combinación de:

•
Structured prompting (similar a Constrained Decoding)

•
Linters (similar a Constitutional AI)

•
Sandboxing (similar a Formal Verification)

Trifecta debería hacer lo mismo: combinar los tres métodos según el caso de uso.

