Hallazgos Clave: Ingeniería Inversa de Factory AI

Arquitectura Central de Factory AI

1. El Inner Loop (Ciclo Interno del Agente)

Factory implementa un ciclo de retroalimentación cerrado que el agente ejecuta continuamente:

Plain Text


Gather Context → Plan → Implement → Run Validation → Submit Reviewable


Este ciclo es el corazón de su arquitectura. No es un simple generador de código, sino un sistema de control con retroalimentación.

2. Componentes Clave de Factory

A. Planning and Task Decomposition

•
Los Droids descomponen problemas complejos en subtareas manejables

•
Usan técnicas de simulación de decisiones y auto-crítica

•
Pueden reflexionar sobre decisiones reales e imaginadas

•
Optimizan trayectorias hacia soluciones óptimas

B. Linters como Guardrails

Factory usa linters como el mecanismo principal de control y validación:

•
Los linters codifican la intención humana en reglas ejecutables

•
Se ejecutan en: dev local, pre-commit, CI, PR bots, y cadena de herramientas del agente

•
Las categorías de lint incluyen:

•
Grep-ability: Formato consistente para búsqueda de texto

•
Glob-ability: Estructura de archivos predecible

•
Architectural Boundaries: Límites de módulos y capas

•
Security & Privacy: Bloqueo de secretos, validación de esquemas, funciones peligrosas

•
Testability & Coverage: Pruebas colocadas junto al código

•
Observability: Logging estructurado y convenciones de telemetría



C. AGENTS.md como Especificación Ejecutable

•
Un archivo que define las normas y convenciones del proyecto

•
Los linters leen estas normas y las hacen cumplir automáticamente

•
El agente usa AGENTS.md para entender "cómo se hacen las cosas aquí"

•
Reemplaza la necesidad de prompts largos y ambiguos

D. Sandboxing y Aislamiento

•
Cada Droid opera en un entorno estrictamente definido y aislado

•
Previene interacciones no intencionadas

•
Auditoría completa de todas las acciones (reversibles)

•
Penetration testing y red-teaming internos

E. Explainabilidad por Diseño

•
Los Droids registran y reportan el razonamiento detrás de cada acción

•
Esto es un componente central de la arquitectura, no un agregado

•
Los desarrolladores pueden validar cada decisión

3. El Flujo de Trabajo Resultante

1.
Agente recibe tarea: "Refactorizar el módulo de autenticación"

2.
Agente lee AGENTS.md: Entiende las convenciones, patrones y límites del proyecto

3.
Agente planifica: Descompone en subtareas (buscar código existente, entender patrones, escribir tests, refactorizar, validar)

4.
Agente implementa: Genera código

5.
Linters validan: Ejecutan automáticamente. Si hay violaciones:

•
El agente recibe feedback claro

•
Intenta autocorregirse (autofix)

•
Itera hasta pasar todos los linters



6.
Agente reporta: Explica qué hizo y por qué

4. Diferencias Clave vs. RAG/Prompt Engineering Tradicional

Aspecto
Tradicional
Factory
Control
Prompts largos y ambiguos
Linters + AGENTS.md (ejecutables)
Validación
Manual o tests posteriores
Automática en cada paso
Escalabilidad
Degradación con complejidad
Mejora con reglas claras
Predictibilidad
Emergente e impredecible
Determinista y verificable
Feedback Loop
Lento (humano)
Rápido (automático)




5. La Innovación Central: Linters como API de Control

Factory ha invertido el paradigma. En lugar de:

•
Intentar que el agente "entienda" el código existente (costoso en tokens)

•
Escribir prompts cada vez más complejos

Factory hace:

•
Define reglas explícitas en linters

•
El agente recibe feedback automático e inmediato

•
El agente se auto-corrige iterativamente

•
"Lint passing" se convierte en la definición de "Done"

Implicaciones para Trifecta-Git

1.
AGENTS.md es más poderoso que skill.md: Factory no solo proporciona instrucciones, sino que las convierte en reglas ejecutables.

2.
Linters son el verdadero control: No es suficiente decirle al agente qué hacer; necesitas validación automática.

3.
El ciclo de retroalimentación es crítico: El agente debe poder iterar rápidamente basándose en feedback automático.

4.
La explainabilidad es arquitectónica: No es un agregado, sino un componente central.



¡Brillante análisis! Has dado en el clavo con la **Ingeniería Inversa** de su modelo. Lo que acabas de describir es el paso de la "Alquimia de Prompts" (mística, impredecible) a la **Ingeniería de Agentes** (determinista, medible).

El hallazgo más disruptivo es el **Punto 5: Linters como API de Control**.
En lugar de *rogarle* al modelo que escriba buen código ("Por favor usa snake_case"), le dejas escribir lo que quiera, le lanzas un linter estricto, y dejas que el **mensaje de error** sea el prompt que corrige al agente. **El error es la instrucción más clara que existe.**

Aquí tienes cómo traducir esta arquitectura corporativa de millones de dólares a tu ecosistema **Trifecta** usando herramientas Open Source y filosofía Unix.

---

### Implementación Práctica en Trifecta: La Arquitectura "Linter-Driven"

Vamos a reemplazar la "esperanza" con "validación automática".

#### 1. El `AGENTS.md`: La Constitución del Proyecto

En lugar de un prompt gigante en el chat, cada repositorio de proyecto tendrá este archivo en la raíz.

**Ubicación:** `/projects/<segment>/AGENTS.md`
**Propósito:** Definir las "Leyes de la Física" de ese proyecto específico.

```markdown
# Normas de Ingeniería para el Proyecto MedLogger

## 1. Arquitectura
- Usamos Clean Architecture estricta.
- NUNCA importes Infraestructura dentro de Dominio.
- Si creas un Caso de Uso, DEBES crear su Test Unitario correspondiente inmediatamente.

## 2. Estilo y Linting
- Python: Seguimos PEP8 estricto + Black formatter.
- No toleramos funciones de más de 20 líneas.

## 3. Seguridad
- Prohibido hardcodear credenciales. Usa `os.getenv`.
- No leas archivos >1MB sin usar streams.

```

**Integración en Trifecta:**
Cuando el agente arranca (`trifecta ctx build`), lo **primero** que se inyecta en su System Context es el contenido de `AGENTS.md`. Es su lectura obligatoria antes de trabajar.

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

#### 3. El Skill de Validación (`trifecta-skills/quality-gate`)

Crearemos un Skill que le dé al agente los comandos para validar su propio trabajo.

**Definición del Skill:**

> "Antes de decir 'He terminado', DEBES ejecutar el comando de validación correspondiente al archivo que tocaste. Si falla, arréglalo tú mismo. No molestes al humano con errores de sintaxis."

**Comandos Permitidos (Alias):**

* `check-python <archivo>` -> Ejecuta `ruff check --output-format=text <archivo>`
* `check-structure <archivo>` -> Ejecuta reglas de `ast-grep` (ej. verificar capas de arquitectura).

### Comparativa: Tu flujo actual vs. Flujo Factory/Trifecta

| Fase | Tu flujo actual (Probable) | Flujo Factory/Trifecta |
| --- | --- | --- |
| **Instrucción** | "Crea un login seguro en Python" | Lee `AGENTS.md` + Prompt Usuario |
| **Generación** | El modelo escribe código de una vez | El modelo escribe, guarda en `/tmp` |
| **Validación** | Tú lees el código y buscas errores | El script ejecuta `ruff` y `ast-grep` |
| **Corrección** | Tú le dices: "Te faltó el tipo de retorno" | El linter le dice: `MissingReturnType` |
| **Entrega** | Copias y pegas código con bugs potenciales | Recibes código que ya compila y pasa reglas |

### Próximo Paso Concreto

Para adoptar esto, no necesitas programar una plataforma compleja. Solo necesitas:

1. Crear un `AGENTS.md` en tu proyecto actual (`MedLogger`).
2. Definir un comando `make validate` (o un script simple) que corra los linters de tu proyecto.
3. Instruir a tu agente actual: **"De ahora en adelante, cada vez que generes código, imagina que ejecutas `make validate`. Si crees que fallaría, corrígelo antes de mostrármelo. Lee `AGENTS.md` para saber las reglas."**

¿Quieres que redactemos una primera versión del `AGENTS.md` para tu proyecto de enfermería/oncología, definiendo reglas de seguridad de datos clínicos?