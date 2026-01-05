d:
Tree-sitter es una librería escrita en C puro que se compila a binarios nativos pequeños o WASM, con bindings para casi todos los lenguajes de scripting (Python, Node.js, Rust). Esto permite que un agente escrito en Python pueda parsear Java, Rust, Go y TypeScript sin necesidad de instalar las toolchains completas de esos lenguajes (JDK, Cargo, npm, etc.), manteniendo el "peso" de la herramienta al mínimo.1
2.2 Estrategia de "Skeleton Maps" (Mapas de Esqueleto)
Una tentación común es intentar indexar cada identificador del código, creando una tabla de símbolos masiva similar a la de un IDE completo. Esto viola el principio de "lean". La estrategia recomendada por la evidencia de campo (implementada exitosamente en herramientas como Aider y Tabby) es la generación de Skeleton Maps.2
Un Skeleton Map es una representación reducida del AST que conserva solo las estructuras de alto nivel necesarias para la navegación y el contexto global, descartando los detalles de implementación (cuerpos de funciones).
Proceso de Construcción:
Utilizando el lenguaje de consultas de Tree-sitter (S-expressions), se extraen selectivamente nodos específicos. Por ejemplo, en Python:
