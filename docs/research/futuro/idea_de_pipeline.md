Aquí tienes el **Informe de Arquitectura Consolidado**. Este documento cura y unifica todas las ideas discutidas (Factory, Programación Funcional, Observabilidad Profunda) en una especificación técnica coherente para el desarrollo de Trifecta.

---

# Especificación Técnica: El Pipeline Trifecta

**Arquitectura de Ejecución Determinista y Observabilidad Funcional para Agentes de IA**

**Fecha:** 30 de diciembre de 2025
**Arquitecto:** Domingo
**Estatus:** Definición de Core

## 1. Visión y Filosofía

El objetivo de Trifecta es transformar la ejecución de agentes de IA de un proceso estocástico ("caja negra") a un proceso de ingeniería determinista ("caja de cristal").
Para lograr esto, abandonamos el paradigma de "chat" y adoptamos el paradigma de **Máquina de Estados Finitos con Arquitectura Funcional**. El Pipeline no es simplemente un ejecutor de tareas; es un sistema de registro inmutable donde la observabilidad es una propiedad intrínseca, no un añadido.

## 2. Fundamentos Arquitectónicos

### 2.1 Inmutabilidad y Estado (`Time Travel Debugging`)

El estado del agente (`AgentState`) se define como una estructura de datos inmutable (`dataclass(frozen=True)`).

* **Principio:** Ninguna función modifica el estado. Cada paso del pipeline consume un estado  y produce un nuevo estado .
* **Persistencia:** Cada transición de estado se serializa. Utilizando **Almacenamiento Direccionable por Contenido (CAS)** (similar a Git), solo guardamos los deltas o referencias hash, permitiendo almacenar miles de pasos eficientemente.
* **Capacidad:** Esto habilita el **Time Travel Debugging**. Podemos cargar el estado exacto del "Paso 4" de una sesión fallida y reanudar la ejecución desde ahí con determinismo absoluto.

### 2.2 Railway Oriented Programming (ROP)

El flujo de ejecución abandona el manejo de excepciones (`try/catch`) en favor de la Mónada `Result` (o `Either`).

* **Vía del Éxito (Success Track):** El agente genera código, pasa validaciones, pasa tests. El estado fluye transformándose.
* **Vía del Fallo (Failure Track):** Si ocurre un error (Linter, Test, Timeout), el flujo cambia de vía. El error no rompe el programa; se encapsula como un objeto de datos (`FailureContext`) que contiene el estado en el momento del fallo y la razón semántica.
* **Beneficio:** Permite que el sistema reaccione lógicamente a los errores (ej. "Intentar auto-corrección") en lugar de crashear.

## 3. Componentes del Pipeline

### 3.1 El Orquestador (The Runner)

Es un bucle de control cerrado que gestiona la vida del agente. No avanza hasta que se cumplen las condiciones de verdad.

1. **Input Estructurado:** Validación estricta de la entrada del usuario (Objetivo + Contexto + Restricciones).
2. **Compilación JIT:** Carga `AGENTS.md` y genera la configuración de los linters en memoria.
3. **Bucle de Ejecución:** Ciclo `Generar -> Validar -> Ejecutar` con un límite de `MAX_RETRIES`.

### 3.2 El Motor de Observabilidad ("Flight Recorder")

En lugar de logs de texto plano, el pipeline emite una **Traza de Eventos Estructurados** (JSONL).
Cada evento es una tupla: `(Timestamp, EventType, Payload, StateHash, Metrics)`.

* **Traceability:** Podemos reconstruir la sesión completa.
* **Meta-Debugging:** Vinculación directa entre un error de ejecución y la regla específica de `AGENTS.md` que se violó. El log no dice "Error", dice "Violación de Regla #3: Arquitectura Limpia".

### 3.3 El Sistema de Métricas (Telemetría MDP)

Tratamos al agente como un Proceso de Decisión de Markov .

* **Fricción de Validación:** ¿Cuántos intentos necesita el agente para pasar el linter? (Métrica de calidad del Prompt).
* **Recompensa ():** Asignación automática de puntos (+10 Test Pass, -5 Linter Fail). Permite evaluar objetivamente si una nueva versión del modelo es "mejor" o "peor".
* **Entropía:** Medición de la "confianza" del modelo en sus decisiones.

## 4. Gobernanza y Seguridad

### 4.1 Mimetismo por Referencia (Reference-Driven Generation)

Para evitar código genérico, el pipeline fuerza la inyección de contexto.

* **Regla:** El agente no puede crear un archivo sin declarar un "Archivo de Referencia" existente en el proyecto.
* **Validación:** `ast-grep` compara la estructura AST del nuevo código con la referencia. Si la similitud estructural es < 80%, se rechaza.

### 4.2 Análisis de Flujo Tóxico (Taint Analysis)

Seguridad estática en el grafo de ejecución.

* Las entradas del usuario se marcan como `TAINTED`.
* El pipeline bloquea cualquier intento de pasar datos `TAINTED` a funciones sensibles (`subprocess`, `eval`, `fs.write`) sin pasar por una función de sanitización certificada.

## 5. Estrategia de Implementación (Hoja de Ruta)

1. **Fase 1: El Núcleo Inmutable.** Definir la clase `AgentState` (Pydantic) y el mecanismo de `Result`. Implementar el loop básico con `instructor` para generación estructurada.
2. **Fase 2: La Jaula de Validación.** Integrar `ast-grep` y `ruff` dentro del pipeline. Implementar la compilación JIT de `AGENTS.md`.
3. **Fase 3: La Caja Negra.** Implementar el `TraceRecorder` que guarda los eventos en `.jsonl` y el sistema de almacenamiento de estados (CAS).
4. **Fase 4: La Interfaz (TUI).** Construir el panel de control en `Textual` que visualiza la traza, los reintentos y permite el "Time Travel" visual.

---

**Conclusión Técnica:**
Esta arquitectura elimina la "suerte" de la ecuación. Al forzar estructura en la entrada, inmutabilidad en el proceso y validación estricta en la salida, Trifecta se convierte en una herramienta de ingeniería de software robusta, capaz de operar con la fiabilidad que un entorno de producción (o crítico como salud) requiere.