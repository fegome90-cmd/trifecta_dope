Plan de Implementación de Trifecta-Git: Un Enfoque Funcional

Para: El Autor De: Editor Técnico Senior Fecha: 30 de diciembre de 2025

Filosofía Central: Un Pipeline de Transformación de Datos

La Programación Funcional (FP) es la metodología perfecta para implementar el sistema Trifecta-Git. La razón es simple: el proceso completo de trifecta ctx build puede ser modelado como un pipeline de transformación de datos puros. No hay estado mutable, solo una serie de funciones que reciben datos, los transforman y pasan el resultado a la siguiente función, culminando en la creación del artefacto context_pack.json.

El Pipeline:

Configuración Inicial -> (f1) -> Estado Deseado -> (f2) -> Estado Actual -> (f3) -> Plan de Ejecución -> (f4) -> Resultado Final

Este enfoque garantiza que el sistema sea declarativo, predecible, componible y fácilmente testeable.

Fases del Plan de Implementación (con enfoque FP)

Fase 1: Definición de los Tipos de Datos Inmutables

El primer paso en un diseño FP es definir las estructuras de datos con las que trabajaremos. Estas serán nuestras "formas" de datos inmutables. En un lenguaje como Python, usaríamos dataclasses con frozen=True o NamedTuple. En TypeScript, interfaces o types.

1.
SkillDeclaration: Representa una entrada en trifecta.yaml (ej. { skill: "url", version: "v1" }).

2.
LockedSkill: Representa una entrada en trifecta-lock.yaml (ej. { url: "url", commit: "hash" }).

3.
ResolvedSkill: Un objeto enriquecido que contiene la declaración, el commit bloqueado y el contenido del archivo markdown de la skill.

4.
ExecutionContext: Un objeto que contiene el estado de la ejecución (configuración del proyecto, skills locales, etc.).

5.
ExecutionPlan: Una lista de acciones a realizar (ej. Clone(url, commit), Copy(source, dest)). Es un plan, no una ejecución.

6.
BuildResult: Un objeto que representa el éxito o fracaso de la operación.

Fase 2: Implementación del Pipeline de Funciones Puras

Aquí se construye el núcleo del comando trifecta ctx build. Cada paso es una función pura que no tiene efectos secundarios.

1.
parse_config(project_path: str) -> ExecutionContext

•
Input: La ruta al proyecto.

•
Output: Un ExecutionContext que contiene los datos leídos de trifecta.yaml y trifecta-lock.yaml.

•
Lógica: Esta es una de las pocas funciones que interactúa con el sistema de archivos (un efecto secundario controlado).



2.
resolve_skill_states(context: ExecutionContext) -> list[ResolvedSkill]

•
Input: El ExecutionContext.

•
Output: Una lista de ResolvedSkill.

•
Lógica: Compara las SkillDeclaration del yaml con las LockedSkill del lock. Determina qué skills necesitan ser clonadas/actualizadas y cuáles ya están satisfechas. Es una función de pura lógica de negocio.



3.
create_execution_plan(resolved_skills: list[ResolvedSkill]) -> ExecutionPlan

•
Input: La lista de ResolvedSkill.

•
Output: Un ExecutionPlan.

•
Lógica: Traduce la lista de skills resueltas en una serie de pasos concretos (ej. [Clone(...), Copy(...)]). Importante: esta función no ejecuta nada, solo describe lo que se debe hacer.



4.
execute_plan(plan: ExecutionPlan) -> BuildResult

•
Input: El ExecutionPlan.

•
Output: Un BuildResult (éxito o fracaso).

•
Lógica: Este es el "intérprete" del plan. Es la segunda función con efectos secundarios (clonar repositorios, escribir archivos). Itera sobre las acciones del plan y las ejecuta. Si algo falla, se detiene y devuelve un error.



5.
generate_context_pack(skills: list[ResolvedSkill], local_ctx: dict) -> dict

•
Input: La lista de ResolvedSkill (con su contenido ya cargado) y el contexto local del proyecto.

•
Output: El diccionario final que se escribirá como context_pack.json.

•
Lógica: Función pura que combina los datos de entrada en la estructura final del artefacto.



Fase 3: Composición y Orquestación

El comando trifecta ctx build se convierte en una simple composición de estas funciones, utilizando un estilo de "pipeline" o "composición de funciones".

Python


# Ejemplo en Python-like pseudocode
from functional import pipe

result = pipe(
    parse_config("./my_project"),
    resolve_skill_states,
    create_execution_plan,
    execute_plan,
    # ... y así sucesivamente
)


Para manejar los posibles errores en cada paso (una lectura de archivo que falla, un plan de ejecución vacío), se puede usar un Result o Either monad, un patrón común en FP. Esto evita el uso de excepciones y hace que el flujo de datos sea explícito.

Python


# Ejemplo con un Result Monad
result = (
    parse_config("./my_project")
    .and_then(resolve_skill_states)
    .and_then(create_execution_plan)
    .and_then(execute_plan)
    .and_then(generate_context_pack)
    .and_then(write_context_pack_to_disk)
)

if result.is_err():
    print(f"Build failed: {result.error()}")


Ventajas de este Plan Funcional

•
Testeabilidad: Cada función pura (resolve_skill_states, create_execution_plan, generate_context_pack) puede ser testeada de forma aislada y determinista. Solo necesitas mockear las funciones con efectos secundarios (parse_config, execute_plan).

•
Predictibilidad: El comportamiento del sistema es fácil de razonar. Los datos fluyen en una sola dirección. No hay estado oculto ni mutaciones inesperadas.

•
Componibilidad: Es fácil añadir nuevos pasos al pipeline (ej. un paso de validación de schema para las skills) sin afectar al resto del sistema.

•
Robustez: El uso de mónadas como Result hace que el manejo de errores sea explícito y robusto, eliminando la necesidad de bloques try/except anidados.

Este plan no solo implementa la funcionalidad requerida, sino que lo hace de una manera que es fiel a la elegancia y claridad de la arquitectura Trifecta, creando un sistema que es tan agradable de mantener como de usar.

==========================================================================================================


Tienes **toda la razón**. Qué bueno que pusiste el freno de mano. 🛑

Como arquitectos, a veces nos enamoramos de la "solución perfecta" (el modelo Neovim/Git es técnicamente hermoso) y olvidamos el principio **YAGNI (You Aren't Gonna Need It)**.

### La Respuesta Honesta: NO.

Para tu escala actual (un desarrollador, múltiples proyectos privados, una sola máquina), montar un gestor de dependencias distribuido con Git, Lockfiles y resolución de versiones es **matar moscas a cañonazos**.

Es **Over-engineering** de manual.

**¿Por qué?**

1. **Complejidad Accidental:** Tendrías que escribir lógica para clonar repos, manejar errores de red, conflictos de merge, autenticación SSH con GitHub... solo para copiar un archivo de texto de 50 líneas.
2. **Fricción:** Si quieres corregir un error tipográfico en tu skill de Python, tendrías que: Editar repo skill -> Commit -> Push -> Ir a proyecto -> Update Lockfile -> Build. **Es demasiado lento.**

---

### La Alternativa Pragmática: "La Librería Local" 📚

Vamos a bajar 3 cambios. Olvida Git y la red.
Tu "Ecosistema" vive en tu disco duro.

**El Diseño Simplificado (KISS):**

1. **Centralización Simple:**
Creas una carpeta en tu máquina: `~/Developer/trifecta-library/`.
Ahí guardas tus `.md` maestros: `python.md`, `tdd.md`, `react.md`.
2. **Referencia Directa:**
Tu `installer.py` (o el builder) simplemente sabe buscar ahí.
*Config (`trifecta.yaml`):*
```yaml
skills:
  - python  # Busca en ~/Developer/trifecta-library/python.md
  - tdd

```


3. **Resolución (Build Time):**
Cuando corres `trifecta ctx build`:
1. El script mira la variable de entorno `TRIFECTA_LIB_PATH`.
2. Lee el archivo `python.md` de ahí.
3. Lo inyecta en el `context_pack.json`.



**Ventajas Inmediatas:**

* **Zero Latency:** Es lectura de disco local. Instantáneo.
* **Edición en Vivo:** Abres `~/Developer/trifecta-library/python.md`, lo editas, corres `build` en tu proyecto y listo. El ciclo de feedback es de segundos, no minutos.
* **Código:** Pasamos de escribir 300 líneas de gestión de Git a escribir 20 líneas de `shutil.copy` o `file.read()`.

### ¿Te hace sentido este "Downgrade"?

Pasamos de un "Sistema de Paquetes Distribuido" a una **"Carpeta de Recursos Compartidos"**. Cumple el 100% de tu necesidad actual (reutilizar skills) con el 1% de la complejidad.

Si estás de acuerdo, **borramos la idea de los Lockfiles y Git**, y simplemente le enseñamos a tu script refactorizado a leer de una variable de entorno `TRIFECTA_LIB_PATH`.

¿Te parece más sensato?


¡Esa es la actitud de un **Arquitecto de Sistemas Críticos**! 🛡️

Tienes toda la razón. "Local" no significa "Seguro".
Si editas tu `python.md` global para probar algo rápido y rompes una regla, no quieres que **todos** tus proyectos se infecten silenciosamente la próxima vez que hagas build. O peor, si un script malicioso modifica tu librería local, tus agentes no deberían ingerir ese veneno.

Para evitar ataques de cadena de suministro (Supply Chain Attacks) y garantizar **Determinismo Absoluto**, la solución no es Git complejo, es **Criptografía Simple**.

Vamos a implementar el **"Content-Addressable Security Model"** (CAS).

### 🔒 La Arquitectura de Seguridad: "Trust on First Use" (TOFU) reforzado

Tu intuición de tener `lockfile`, `read-only` y `reportes` es correcta. Así es como lo implementaremos sin la complejidad de Git:

#### 1. El Manifiesto (`trifecta.yaml`) - La "Allowlist"

Solo lo que está aquí entra. Si un archivo existe en tu librería pero no está aquí, el builder lo ignora.

```yaml
# Intención (Editable por humanos)
skills:
  - name: python-expert
    path: "~/Developer/trifecta-lib/python.md"
  - name: tdd-strict
    path: "~/Developer/trifecta-lib/tdd.md"

```

#### 2. El Candado (`trifecta.lock`) - La "Verdad Criptográfica"

Aquí no guardamos versiones (v1.0), guardamos **Hashes (SHA-256)** del contenido.

```yaml
# Realidad (Generado por máquina - READ ONLY para humanos)
locks:
  python-expert:
    source: "~/Developer/trifecta-lib/python.md"
    sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    last_verified: "2025-12-30T17:00:00Z"

```

#### 3. El Guardián (The Builder Protocol)

Aquí es donde matamos el riesgo de Supply Chain. Cuando ejecutas `ctx build`:

1. **Lectura:** El builder lee el archivo local `python.md`.
2. **Hashing:** Calcula el SHA-256 del contenido actual en memoria.
3. **Verificación (The Gate):**
* Compara el Hash Calculado vs. Hash en `trifecta.lock`.
* **¿Coinciden?** ✅ Procede. Inyecta el contenido.
* **¿No Coinciden?** ❌ **STOP CRÍTICO**.
* *Alerta:* "Security Mismatch! El archivo `python.md` ha cambiado desde la última vez. El contenido no es confiable."
* *Acción:* El build falla. No se genera nada.





#### 4. La Actualización Explícita (`ctx update`)

Para aceptar el cambio (por ejemplo, editaste la skill legítimamente), debes ejecutar un comando consciente:

```bash
trifecta ctx update --skill python-expert

```

Este comando:

1. Calcula el nuevo hash.
2. Te muestra un **diff** (Reporte) de qué cambió.
3. Actualiza el `trifecta.lock` con el nuevo hash.

---

### 🛡️ Por qué esto cumple tus requisitos

| Requisito | Implementación |
| --- | --- |
| **Lockfile Obligatorio** | Si no hay lockfile o no coincide el hash, el build falla. |
| **Read Only** | El builder nunca toca los archivos fuente, solo lee y verifica. |
| **Allowlist** | Solo se procesan las entradas explícitas en `trifecta.yaml`. |
| **Update Explícito** | Los cambios en la librería no se propagan solos. Requieren intervención humana (`ctx update`). |
| **Reportes** | El `ctx update` genera un diff de seguridad antes de aceptar. |

### 🚦 Plan de Acción Refinado (Seguridad)

Ahora sí, definamos los modelos de datos con esta capa de seguridad.

**Paso 1:** Implementar la lógica de Hashing y Verificación en el Dominio.
**Paso 2:** Crear el flujo de `lock` y `verify`.

Aquí tienes el prompt para el agente, enfocado en **Integridad de Datos**.

---

### PROMPT: IMPLEMENT SECURE MANIFEST & LOCKING (SHA-256)

**Role:** Security Architect.

**Context:**
We are implementing a **Secure Local Dependency System** for Trifecta Skills.
To prevent Supply Chain attacks (unintended changes in source files), we will use a **Content-Addressable Locking mechanism** (SHA-256).

**Architecture Rules:**

1. **Manifest (`trifecta.yaml`):** Declares intent (path to file).
2. **Lockfile (`trifecta.lock`):** Stores the approved SHA-256 hash of the content.
3. **Strict Verification:** The builder MUST fail if the current file content hash does not match the lockfile hash.
4. **Explicit Update:** Only a dedicated `update` command can write to the lockfile.

**Mission:**
Implement the Domain Models and Logic to support this security protocol.

**Tasks:**

1. **Create `src/domain/security.py`:**
* Function `calculate_file_hash(path: Path) -> str`: Returns SHA-256 hex digest.


2. **Create `src/domain/manifest.py`:**
* `SkillEntry`: `name` (str), `path` (Path).
* `LockEntry`: `name` (str), `sha256` (str), `source_path` (str), `updated_at` (datetime).
* `TrifectaManifest`: List of `SkillEntry`.
* `TrifectaLock`: Dict of `name` -> `LockEntry`.


3. **Define Logic (Mock in comments):**
* Explain how `validate_integrity(manifest, lock)` will work.
* Explain how `update_lock(manifest)` will work.



**Output:**
Show the Python code for `security.py` and `manifest.py`.

---
