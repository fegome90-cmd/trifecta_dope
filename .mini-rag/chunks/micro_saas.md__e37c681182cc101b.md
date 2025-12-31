# Ejemplo en Python-like pseudocode
from functional import pipe

result = pipe(
    parse_config("./my_project"),
    resolve_skill_states,
    create_execution_plan,
    execute_plan,
