tión de Recursos Activa: Limitar a 1 servidor activo a la vez si la RAM es baja. Implementar TTL (Time-to-Live) para matar servidores inactivos tras 5 min.
4. Dirty State Complexity
Inconsistencia entre VFS y disco si el agente crashea.
Atomicidad: El VFS debe ser la única fuente de verdad. Al iniciar, siempre limpiar el estado del LSP (didClose/didOpen) para asegurar sincronía con el disco.
5. Fallos de Parsing (Lenguajes Mixtos)
Tree-sitter falla en archivos con templating (Jinja, PHP+HTML).
Inyecciones de Lenguaje: Configurar Tree-sitter para soportar "language injections" (parsear JS dentro de HTML). Fallback elegante a búsqueda de texto plano si el parser falla.
