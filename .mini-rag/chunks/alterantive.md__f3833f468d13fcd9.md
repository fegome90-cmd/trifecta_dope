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
