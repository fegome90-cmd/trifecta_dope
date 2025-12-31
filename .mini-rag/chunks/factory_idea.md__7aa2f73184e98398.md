#### 3. El Skill de Validación (`trifecta-skills/quality-gate`)

Crearemos un Skill que le dé al agente los comandos para validar su propio trabajo.

**Definición del Skill:**

> "Antes de decir 'He terminado', DEBES ejecutar el comando de validación correspondiente al archivo que tocaste. Si falla, arréglalo tú mismo. No molestes al humano con errores de sintaxis."

**Comandos Permitidos (Alias):**

* `check-python <archivo>` -> Ejecuta `ruff check --output-format=text <archivo>`
* `check-structure <archivo>` -> Ejecuta reglas de `ast-grep` (ej. verificar capas de arquitectura).
