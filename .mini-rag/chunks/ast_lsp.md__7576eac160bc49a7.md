### T4. Spec Selector v0 + Resolver AST

**Selector v0 propuesto:**
`sym://<lang>/<qualified_name>` (ej. `sym://py/package.module/AuthManager#login`)
**DoD**

* Resolver AST: selector → (path, range)
* Ambigüedad: devuelve lista de candidatos y aborta (fail-closed).
  **Tests**
* Ambiguity test: dos símbolos con mismo nombre → debe pedir desambiguación.
* Drift test: insertar líneas arriba → resolver sigue encontrando método correcto.
  **Métrica**
* `selector_resolve_success_rate`
* `patch_failed_rate` (debe bajar con selector vs línea)

---
