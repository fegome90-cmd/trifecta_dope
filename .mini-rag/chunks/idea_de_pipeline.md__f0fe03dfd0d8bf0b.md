### 4.1 Mimetismo por Referencia (Reference-Driven Generation)

Para evitar código genérico, el pipeline fuerza la inyección de contexto.

* **Regla:** El agente no puede crear un archivo sin declarar un "Archivo de Referencia" existente en el proyecto.
* **Validación:** `ast-grep` compara la estructura AST del nuevo código con la referencia. Si la similitud estructural es < 80%, se rechaza.
