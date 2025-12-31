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
