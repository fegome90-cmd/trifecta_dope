### T1. AST Engine + Grammar packaging

**Descripción:** integrar Tree-sitter y cargar gramáticas para el lenguaje objetivo.
**DoD**

* Parser inicializa y parsea archivos del repo objetivo.
* Manejo de errores: si un archivo no parsea → registra y sigue (no abort).
  **Tests**
* Unit: parsea archivo válido y uno con error sintáctico (no explota).
* Perf: parse de N archivos bajo un budget (define baseline).
  **Métrica**
* `ast_parse_success_rate >= 95%` (excluyendo templates raros)
* `ast_parse_time_total` (baseline por repo)
