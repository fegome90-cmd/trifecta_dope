```



### Conclusión del Editor Técnico

Tu propuesta de `AGENTS.md` es viable y muy potente.
El cambio clave es **no inventar tu propio motor de linting**. Usa `AGENTS.md` como una **Interfaz de Alto Nivel** que orquesta herramientas de bajo nivel (`ast-grep`, `ruff`, `biome`) que ya están optimizadas en Rust.

**Siguiente paso sugerido:**
¿Implementamos la regla `naming-convention` en el compilador Python? Es un excelente caso de uso para expresiones regulares dentro de `ast-grep`.
