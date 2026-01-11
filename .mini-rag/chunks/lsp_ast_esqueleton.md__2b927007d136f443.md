s.
5.1 Matriz de Decisión Tecnológica
Componente
Opción Recomendada
Justificación "Lean"
Trade-offs
Motor AST
Tree-sitter (Python bindings)
<1ms latencia, robusto a errores, sin deps externas pesadas.
Requiere mantener gramáticas (.so/.dll) para cada lenguaje.
Cliente LSP
Multilspy (Wrapper)
Abstrae la gestión de procesos y JSON-RPC. Probado en producción (VS Code).
Overhead de Python. Curva de aprendizaje de su API.
Indexación
Skeleton Map (In-Memory)
Carga instantánea, bajo consumo RAM. Suficiente para navegación global.
Menos detallado que SCIP/LSIF. No soporta queries complejas offline.
Direccionamiento
Selectores Semánticos
Resistente a drift. Elimina errores de línea.
Requiere implementar un resolver lógico sobre el AST.
Caché
Hash Estructural
Evita re-análisis por cambios cosméticos.
Costo computacional de calcular hashes de árboles.
