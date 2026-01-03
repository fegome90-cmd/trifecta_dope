Plan de Implementación Revisado: Trifecta con Functional Programming

Para: Domingo (Lead Architect) De: Ingeniero Senior, Desarrollo Agéntico Fecha: 30 de diciembre de 2025 Asunto: Especificación de Desarrollo FP para Trifecta v1.1

1. Filosofía Central: El Pipeline de Transformación Inmutable

Abandonamos el modelo de "orquestador con un loop" en favor de un pipeline de transformación de datos puros. Cada paso del proceso es una función que toma datos inmutables y devuelve nuevos datos inmutables, sin efectos secundarios.

El estado no se "mantiene", se transforma.

2. El Pipeline Funcional de Trifecta

El flujo completo se modela como una composición de funciones:

Python


# Pseudocódigo funcional

initial_request: Request = ...

result: Result[FinalCode, Error] = (
    parse_request(initial_request)
    .and_then(load_constitution)
    .and_then(compile_linter_config_in_memory)
    .and_then(run_generative_loop)
    .and_then(run_user_test)
)

# El resultado se maneja al final
match result:
    case Ok(final_code):
        commit_to_disk(final_code)
    case Err(error):
        log_error(error)


3. Especificación de Fases (Funciones Puras)

Fase 1: Tipos de Datos Inmutables (El "Mundo")

Definimos las estructuras de datos que fluyen por el pipeline. Usaremos dataclasses con frozen=True en Python.

•
Request(goal, context, constraints)

•
Constitution(rules)

•
LinterConfig(rules)

•
AgentState(request, constitution, linter_config, current_code, history)

•
AgentOutput(code, test, justification)

•
LinterResult(passed, errors)

•
TestResult(passed, output)

•
FinalCode(code, test)

•
Error(type, message)

Fase 2: El Pipeline de Funciones Puras

Cada función toma un estado y devuelve un Result monad (Ok(nuevo_estado) o Err(error)).

1. parse_request(request: dict) -> Result[Request, Error]

•
Valida la entrada del usuario. Devuelve un objeto Request inmutable.

2. load_constitution(request: Request) -> Result[AgentState, Error]

•
Lee AGENTS.md.

•
Devuelve el estado inicial AgentState con la constitución cargada.

3. compile_linter_config_in_memory(state: AgentState) -> Result[AgentState, Error]

•
Parsea las reglas de la constitución.

•
Genera la configuración del linter en memoria.

•
Devuelve un nuevo AgentState con linter_config poblado.

4. run_generative_loop(state: AgentState) -> Result[AgentState, Error]

•
Esta es la única función con un loop, pero es un loop de transformación de datos, no de estado.

•
Usa tail recursion o un reduce funcional.

Python


# Pseudocódigo del loop funcional
def run_generative_loop(state, max_retries):
    if max_retries == 0:
        return Err("Max retries reached")

    # Generación
    agent_output = generate_code(state) # Pura

    # Validación
    linter_result = run_linter(state.linter_config, agent_output.code) # Pura

    # Decisión
    if linter_result.passed:
        new_state = state.update(current_code=agent_output.code) # Inmutable
        return Ok(new_state)
    else:
        feedback = create_feedback(linter_result) # Pura
        new_state = state.add_to_history(feedback) # Inmutable
        return run_generative_loop(new_state, max_retries - 1) # Recursión


5. run_user_test(state: AgentState) -> Result[FinalCode, Error]

•
Ejecuta el test del usuario contra el código validado.

•
Si pasa, devuelve Ok(FinalCode).

•
Si falla, devuelve Err(TestFailed).

Fase 3: Composición con Mónadas (Result)

El uso de Result (o Either en otros lenguajes) es no negociable. Elimina la necesidad de try/except y hace que el flujo de errores sea explícito y seguro.

Python


# Ejemplo de la librería `returns` en Python
from returns.result import Result, Ok, Err

def process(data) -> Result[str, str]:
    # ...

# El pipeline se compone con .bind (o .and_then)
result = (
    process(initial_data)
    .bind(another_process)
    .bind(yet_another_process)
)


4. Ventajas de Este Enfoque Revisado

Aspecto
Beneficio
Testeabilidad
Máxima. Cada función es pura y se puede testear de forma aislada.
Predictibilidad
Total. El mismo input siempre produce el mismo output.
Componibilidad
Extrema. Se pueden añadir nuevos pasos al pipeline sin afectar el resto.
Robustez
El manejo de errores es explícito y a prueba de fallos.
Simplicidad
La lógica es lineal y fácil de seguir, sin estado mutable oculto.




5. Hoja de Ruta de Desarrollo FP

Fase 1: El "Mundo" y el Result

•
Implementar las dataclasses inmutables.

•
Elegir e integrar una librería de mónadas (returns en Python es una buena opción).

Fase 2: El Pipeline Básico

•
Implementar parse_request, load_constitution y compile_linter_config_in_memory.

•
Componerlos en un pipeline simple.

Fase 3: El Loop Generativo

•
Implementar run_generative_loop usando recursión o reduce.

•
Integrar instructor y ast-grep como funciones puras que devuelven datos.

Fase 4: El Final del Camino

•
Implementar run_user_test y la lógica final de commit_to_disk (el único punto con efectos secundarios, aislado al final).

6. Conclusión

Este plan no solo corrige los antipatrones, sino que eleva la arquitectura a un nivel superior de elegancia y robustez. Es la encarnación de la filosofía de Trifecta: control, predictibilidad y belleza a través de la simplicidad funcional.
