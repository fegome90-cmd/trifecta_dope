### T2. Generar Skeleton Map (defs + firmas) + cache

**Descripción:** recorrer repo y extraer solo definiciones de alto nivel (clases/funciones/métodos).
**DoD**

* Produce `ast_skeleton.json` (o sqlite liviano) con: `symbol_id`, `kind`, `qualified_name`, `path`, `range`, `signature`.
* Cache por `repo_sha` y `file_sha` (hash textual basta por ahora).
  **Tests**
* Golden test: skeleton esperado para un mini-repo fixture.
* Cache test: cambio cosmético en cuerpo NO obliga rebuild total (si aún no haces hash estructural, al menos limita rebuild por archivo).
  **Métrica**
* `skeleton_build_time`, `skeleton_size_bytes`, `avg_symbols_per_file`
