3.4 Gestión de Latencia y "Cold Start"
Los servidores LSP como rust-analyzer o Eclipse JDT.LS son notorios por sus tiempos de arranque e indexación inicial, que pueden durar minutos en monorepos grandes.25 Esto es inaceptable para un agente CLI que se espera que responda en segundos.
Estrategias de Mitigación:
Arquitectura de Demonio Persistente: El cliente LSP no debe ser efímero (arrancar y morir con cada comando). Debe implementarse como un demonio en segundo plano (lanser-daemon) que mantiene el servidor LSP "caliente" entre invocaciones del agente CLI.
Fallback Híbrido: Si el servidor LSP está inicializando ("Cold Start"), el agente no debe bloquearse. Debe degradarse automáticamente a usar el índice de Tree-sitter (que es instantáneo) para navegación básica, y solo usar LSP cuando esté listo. Esta estrategia de "Progressive Enhancement" asegura operatividad constante.9
4. Arquitecturas de Agentes y Estrategias de Recuperación
La combinación de AST y LSP habilita arquitecturas de recuperación de contexto que son deterministas y estructuralmente conscientes, superando las limitaciones de los embeddings.
4.1 "Repo Map" Basado en Grafos y PageRank (Caso Aider)
El proyecto Aider ha popularizado una técnica altamente efectiva para comprimir el contexto de un repositorio entero en el prompt del sistema.
Implementación:
Extracción: Usar Tree-sitter para identificar todas las defi
