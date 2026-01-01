Perfecto. Tomo tu informe como “input” y lo convierto en **plan de sprint lean**, con tickets, DoD, tests y métricas. El objetivo es **AST + LSP precisos y concisos**, sin construir un IDE dentro de Trifecta. 🧰

> Referencias base (para no inventar): LSP spec 3.17 ([Microsoft en GitHub][1]), Tree-sitter incremental parsing ([Tree-sitter][2]), TypeScript LSP wrapper (typescript-language-server) ([Homebrew Formulae][3]).

---

# Sprint: AST+LSP Lean (v0) — “Precisión primero, lectura mínima”

**Duración sugerida:** 1 sprint (1–2 semanas).
**Sprint Goal:** que el agente pueda **localizar y traer snippets correctos** (sin abrir archivos completos) usando **Skeleton Map (Tree-sitter)** y **LSP on-demand** (1 lenguaje primero).

## Alcance (Scope)

* ✅ **AST Skeleton Map** + comandos CLI (map/locate/snippet)
* ✅ **Selector v0** (semántico mínimo) para evitar drift
* ✅ **LSP on-demand** para **1 lenguaje** (recomiendo **Python con Pyright**) y set mínimo de requests
* ✅ **Progressive disclosure v0** (map → snippet → archivo *solo si* gate)
* ✅ **Probe log mínimo** (evidencia de queries AST/LSP)

## No-alcance (Non-goals) 🚫

* ❌ Shadow Workspace/VFS completo vía `didChange` (postergar)
* ❌ PageRank/graph ranking (postergar)
* ❌ Multi-lenguaje completo (elige 1 primero)
* ❌ Bundles/Background (solo probe log mínimo)

---

# Backlog priorizado (tickets)

## P0 — AST Skeleton Map (Tree-sitter) 🦴

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

### T3. CLI commands: `ast symbols`, `ast locate`, `ast snippet`

**Descripción:** herramientas mínimas para que el agente navegue sin abrir todo.
**DoD**

* `ast symbols --query AuthManager` lista candidatos.
* `ast locate sym://py/...` devuelve rango actual.
* `ast snippet sym://... --lines 30` devuelve contexto acotado.
  **Tests**
* CLI e2e con fixtures.
* Si símbolo no existe → salida fail-closed (no inventa).
  **Métrica**
* `snippet_bytes_served` (debe bajar vs “read file”)

---

## P0 — Selector Semántico v0 (anti-drift) 🎯

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

## P0 — LSP On-demand (1 lenguaje) 🧠

### T5. LSP Client headless mínimo (stdio JSON-RPC)

**Lenguaje recomendado para Sprint:** Python con Pyright (`pyright-langserver`).
La LSP spec define JSON-RPC y los eventos clave. ([Microsoft en GitHub][1])
**DoD**

* Arranca servidor, handshake initialize/initialized.
* Timeout duro (ej. 5s). Si excede → fallback AST.
* Cierre limpio del proceso.
  **Tests**
* Unit: mock JSON-RPC framing.
* Integration: arranca pyright y responde `hover` en fixture repo.
  **Métrica**
* `lsp_cold_start_ms` (P50/P95)
* `lsp_timeout_rate` (debe ser bajo, o fallback siempre)

### T6. Set mínimo de requests LSP

**Implementar solo:**

* `textDocument/definition`
* `textDocument/references`
* `textDocument/hover`
* `textDocument/publishDiagnostics` (capturar notificaciones) ([Microsoft en GitHub][4])
  **DoD**
* `lsp definition selector` retorna location(s)
* `lsp hover selector` retorna firma/docstring
* `diagnostics` se captura y se puede consultar
  **Tests**
* Hover devuelve algo no vacío en símbolo conocido.
* Diagnostics: introducir error en fixture y comprobar que lo reporta.
  **Métrica**
* `lsp_request_success_rate`
* `diagnostics_latency_ms`

---

## P1 — Progressive Disclosure v0 (control de costo) 🪜

### T7. Router/Gate de niveles: map → snippet → file

**Regla:** por defecto **NO leer archivo completo**. Solo si:

* no basta snippet, o
* hay ambigüedad que requiere más evidencia, o
* el usuario pide explícitamente.
  **DoD**
* El agente primero consulta skeleton → luego snippet.
* Lectura full file queda detrás de un gate explícito.
  **Tests**
* En tareas de navegación, bytes leídos deben bajar vs baseline.
* Gate: si intenta full file sin razón → FAIL.
  **Métrica**
* `bytes_read_per_task` ↓
* `accuracy_top1` >= baseline
* `fallback_rate` no sube más de X

---

## P1 — Probe log mínimo (evidencia barata) 🧾

### T8. `probe_events.jsonl` append-only para AST/LSP

**DoD**

* Registra: `ast_query`, `lsp_request`, `lsp_response_meta`, `repo_sha`, `dirty`, `file_sha`, `duration_ms`, `execution_order`.
* No guarda contenido completo; guarda hashes + paths + ranges.
  **Tests**
* Append-only, orden monotónico.
* No filtra secretos (no logging de contenido).
  **Métrica**
* `probe_event_coverage` (≥90% de queries instrumentadas)

---

# Definition of Done del Sprint (PASS/FAIL)

✅ PASS si se cumple todo esto:

1. AST skeleton funciona y responde “¿dónde está X?” sin abrir archivos completos.
2. LSP on-demand para Python funciona con `definition/hover/diagnostics`, con timeout + fallback.
3. Progressive disclosure reduce `bytes_read_per_task` sin bajar `accuracy_top1` (o manteniéndola).
4. Probe log produce evidencia mínima por run.

---

# Burn-down (orden de ejecución recomendado)

1. **T1–T3** (AST end-to-end)
2. **T4** (Selector v0)
3. **T5–T6** (LSP mínimo + fallback)
4. **T7** (Progressive disclosure gate)
5. **T8** (Probe log)

---

# Nota dura (para evitar el transatlántico 🚢)

* **No metas VFS/didChange** en este sprint: es donde se mueren los MVPs.
* **No metas multi-lenguaje**: gana 1 lenguaje con excelencia, luego expandes.
* **No metas ranking PageRank** hasta que tengas métricas que lo justifiquen.



[1]: https://microsoft.github.io/language-server-protocol/?utm_source=chatgpt.com "Official page for Language Server Protocol"
[2]: https://tree-sitter.github.io/?utm_source=chatgpt.com "Tree-sitter: Introduction"
[3]: https://formulae.brew.sh/formula/typescript-language-server?utm_source=chatgpt.com "typescript-language-server"
[4]: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/?utm_source=chatgpt.com "Language Server Protocol Specification - 3.17"
