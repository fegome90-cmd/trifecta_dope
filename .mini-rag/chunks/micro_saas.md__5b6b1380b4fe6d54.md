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
