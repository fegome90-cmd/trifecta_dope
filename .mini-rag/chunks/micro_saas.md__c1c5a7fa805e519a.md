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
