•
Observability: Logging estructurado y convenciones de telemetría



C. AGENTS.md como Especificación Ejecutable

•
Un archivo que define las normas y convenciones del proyecto

•
Los linters leen estas normas y las hacen cumplir automáticamente

•
El agente usa AGENTS.md para entender "cómo se hacen las cosas aquí"

•
Reemplaza la necesidad de prompts largos y ambiguos

D. Sandboxing y Aislamiento

•
Cada Droid opera en un entorno estrictamente definido y aislado

•
Previene interacciones no intencionadas

•
Auditoría completa de todas las acciones (reversibles)

•
Penetration testing y red-teaming internos

E. Explainabilidad por Diseño

•
Los Droids registran y reportan el razonamiento detrás de cada acción

•
Esto es un componente central de la arquitectura, no un agregado

•
Los desarrolladores pueden validar cada decisión

3. El Flujo de Trabajo Resultante

1.
Agente recibe tarea: "Refactorizar el módulo de autenticación"

2.
Agente lee AGENTS.md: Entiende las convenciones, patrones y límites del proyecto

3.
Agente planifica: Descompone en subtareas (buscar código existente, entender patrones, escribir tests, refactorizar, validar)

4.
Agente implementa: Genera código

5.
Linters validan: Ejecutan automáticamente. Si hay violaciones:

•
El agente recibe feedback claro

•
Intenta autocorregirse (autofix)

•
Itera hasta pasar todos los linters
