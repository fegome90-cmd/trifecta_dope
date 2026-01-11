pecific Language) semántico.4
Concepto: En lugar de referenciar coordenadas físicas, el agente referencia rutas lógicas.
Sintaxis Ejemplo: py://modulo/Clase#metodo o ast://FunctionDefinition[name='process_data'].
Resolución Determinista: El sistema (cliente LSP + Tree-sitter) resuelve este selector a las coordenadas físicas actuales (Range) en el momento exacto de la ejecución. Si el archivo cambió, el sistema re-escanea el AST para encontrar dónde está ahora la función process_data, garantizando que la edición se aplique en el lugar correcto.
Beneficio: Elimina prácticamente los errores de "patch failed" y reduce la necesidad de que el agente vuelva a leer el archivo completo para recalcular líneas.
4.3 Process Rewards y Validación Paso a Paso
Integrar LSP permite implementar un sistema de Process Rewards (Recompensas de Proceso) para el aprendizaje o guiado del agente. En lugar de esperar al final para ver si el código funciona, el agente recibe una recompensa positiva inmediata si una acción intermedia (e.g., un renombrado) es validada por el LSP (sin errores de diagnóstico).4 Esto alinea el bucle de planificación del agente con la realidad programática del compilador.
5. Diseño Propuesto: Implementación MVP Lean
Para transformar esta investigación en acción, se propone un diseño en tres hitos incrementales.
5.1 Matriz de Decisión Tecnológica
Componente
Opción Recomendada
Ju
