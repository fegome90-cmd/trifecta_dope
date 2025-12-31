### 3.1 El Orquestador (The Runner)

Es un bucle de control cerrado que gestiona la vida del agente. No avanza hasta que se cumplen las condiciones de verdad.

1. **Input Estructurado:** Validación estricta de la entrada del usuario (Objetivo + Contexto + Restricciones).
2. **Compilación JIT:** Carga `AGENTS.md` y genera la configuración de los linters en memoria.
3. **Bucle de Ejecución:** Ciclo `Generar -> Validar -> Ejecutar` con un límite de `MAX_RETRIES`.
