5.2 Hoja de Ruta de Implementación (3 Hitos)
Hito 1: Conciencia Estructural (AST + Repo Map)
Objetivo: El agente puede navegar la estructura del proyecto sin leer archivos completos.
Entregables:
Integración de tree-sitter y py-tree-sitter.
Generador de "Skeleton Map": script que recorre recursivamente el directorio, parsea archivos y extrae definiciones (Clases, Funciones) a una estructura JSON/Tree.
Implementación de comando /map: Inyecta la representación textual del mapa en el contexto.
DoD: El agente responde correctamente "¿En qué archivo está definida la clase AuthManager?" usando solo el mapa.
Tests: Parseo de repositorios grandes (>10k archivos) en <5s. Resistencia a archivos con errores de sintaxis intencionales.
Hito 2: Inteligencia Semántica (LSP On-Demand)
Objetivo: Resolución precisa de símbolos y documentación.
Entregables:
Implementación de cliente LSP headless (basado en multilspy).
Soporte para pyright (Python) y tsserver (JS/TS).
Herramientas para el agente (Tools): lookup_symbol(name), get_hover(selector), find_references(selector).
Gestión de procesos: Demonio que mantiene el LSP vivo.
DoD: El agente puede navegar desde una llamada a función hasta su definición exacta y recuperar su docstring.
Rollback: Si el LSP falla o tarda >5s, fallback automático a búsqueda por nombre en el índice AST del Hito 1.
Hito 3: Edición Segura (Shadow Workspace)
Objetivo: Edic
