## C) L0 Skeleton: Definición real

- **Artefacto**: Es una transformación funcional del `text` del chunk realizada en tiempo de ejecución por `ContextService._skeletonize`.
- **Campos incluidos**:
  - Headings Markdown (`#`).
  - Bloques de código (```).
  - Primeras líneas de bloques de código que contienen signatures (`def`, `class`, `interface`, `function`, `const`, `var`).
- **Pipeline**: `ctx get --mode skeleton` -> `ContextService.get` -> `_skeletonize`.
- **NO incluye**: Implementaciones de funciones, comentarios de línea (no-headers), imports masivos.
