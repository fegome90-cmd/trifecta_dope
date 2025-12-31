### 4.2 Análisis de Flujo Tóxico (Taint Analysis)

Seguridad estática en el grafo de ejecución.

* Las entradas del usuario se marcan como `TAINTED`.
* El pipeline bloquea cualquier intento de pasar datos `TAINTED` a funciones sensibles (`subprocess`, `eval`, `fs.write`) sin pasar por una función de sanitización certificada.
