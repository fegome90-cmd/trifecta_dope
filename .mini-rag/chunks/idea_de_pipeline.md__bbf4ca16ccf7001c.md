### 2.1 Inmutabilidad y Estado (`Time Travel Debugging`)

El estado del agente (`AgentState`) se define como una estructura de datos inmutable (`dataclass(frozen=True)`).

* **Principio:** Ninguna función modifica el estado. Cada paso del pipeline consume un estado  y produce un nuevo estado .
* **Persistencia:** Cada transición de estado se serializa. Utilizando **Almacenamiento Direccionable por Contenido (CAS)** (similar a Git), solo guardamos los deltas o referencias hash, permitiendo almacenar miles de pasos eficientemente.
* **Capacidad:** Esto habilita el **Time Travel Debugging**. Podemos cargar el estado exacto del "Paso 4" de una sesión fallida y reanudar la ejecución desde ahí con determinismo absoluto.
