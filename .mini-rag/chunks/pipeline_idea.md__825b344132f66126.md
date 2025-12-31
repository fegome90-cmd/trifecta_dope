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
