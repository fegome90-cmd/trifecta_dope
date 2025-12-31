#### 2. "Linters as Guardrails": La Herramienta de Validación

Aquí es donde usamos herramientas estándar de Neovim/Unix para simular el motor de Factory.

Necesitamos linters que sean rápidos y den salida estructurada (JSON o texto claro) que el agente pueda leer.

* **Sintaxis y Estilo:** `ruff` (Python) o `biome` (JS/TS). Son instantáneos.
* **Estructura:** `ast-grep`. Puedes escribir reglas personalizadas ("Si hay un `import` de `infrastructure` en la carpeta `domain`, lanza error").
* **Tipado:** `mypy` o `tsc`.

**El Flujo "Auto-Fix" (El Loop):**

El agente no entrega el código al usuario inmediatamente. El script de Trifecta debe interceptarlo:

1. **Agente:** Genera archivo `auth_service.py`.
2. **Trifecta (Script):** Ejecuta `ruff check auth_service.py`.
* *Resultado:* `Error: Line 15. Variable 'x' is ambiguous.`


3. **Trifecta (Script):** Captura el error y se lo devuelve al Agente como un "User Message" automático.
* *Mensaje al Agente:* "Tu código falló la validación. Error: [log]. Arréglalo."


4. **Agente:** Lee el error, entiende exactamente qué falló, reescribe.
5. **Trifecta:** Vuelve a ejecutar `ruff`.
* *Resultado:* `Clean.`


6. **Trifecta:** Solo AHORA muestra el código a Domingo o hace el commit.
