# Auditoría de Preparación Técnica: Implementación de AST+LSP en Trifecta

**Fecha:** 2026-01-01  
**Rol:** Auditor de Preparación Técnica  
**Objetivo:** Identificar unknowns, decisiones críticas y riesgos ANTES de implementar AST+LSP  
**Criterio de Éxito:** Documento listo para iniciar sprint sin adivinanzas técnicas

---

## EXECUTIVE SUMMARY (12 líneas)

Trifecta ha construido una arquitectura limpia de context-calling (Python 3.12+, Typer CLI, Pydantic models, Clean Architecture) con infraestructura de telemetría local-first y Progressive Disclosure implementada. **La integración de AST+LSP es viable**, pero requiere resolver **3 decisiones críticas** y enfrentar **3 unknowns de alto riesgo**.

### 3 Decisiones Críticas
1. **Lenguaje objetivo del MVP:** Python FIRST (disponible en repo), TS/JS SECOND (no presentes), otros deferred.  
2. **Estrategia LSP:** Arquitectura headless con demonio persistente, fallback a Tree-sitter instantáneo si cold-start.  
3. **Punto de integración:** Nuevo submódulo `src/infrastructure/ast_lsp.py` + hooks en `ContextService.search()` para "symbol-first" routing.

### 3 Unknowns Más Peligrosos
1. **¿Dónde instalar binarios LSP?** (pyright, rust-analyzer): venv vs sistema global vs embedded WASM.  
2. **¿Qué pasa si el servidor LSP cae/diverge?** Sin especificación de "shadow workspace" sync, riesgo de stale data.  
3. **¿Cómo medir caché hit rate de skeleton maps?** Sin métricas existentes, no hay validación cuantitativa.

---

## I. SCOPE REAL: LENGUAJES Y TOOLING

### A. Lenguajes en el Repositorio

| Lenguaje | Presencia | Líneas Est. | Prioridad | Notas |
|----------|-----------|------------|-----------|-------|
| **Python** | ✅ Core | ~3500 (src/) | 🔴 P0 | Typer CLI, domain models, use cases, tests |
| **TypeScript/JavaScript** | ❌ None | 0 | 🔵 P2 | No presente. Roadmap v2 menciona posible soporte futuro. |
| **YAML** | ✅ Config | ~500 | 🟡 P1 | Aliases, trifecta_config.json (pero pydantic valida). |
| **Markdown** | ✅ Docs | ~5000 | 🟡 P1 | templates.py genera .md. Análisis sintáctico minimal. |

**Recomendación MVP:** Tree-sitter para Python (P0), Markdown skeleton maps (P1). Defer TypeScript hasta post-MVP.

---

### B. Infraestructura Actual de Procesos y Tooling

| Aspecto | Estado | Detalles | Riesgo |
|--------|--------|---------|--------|
| **CLI Framework** | ✅ Typer 0.21.0 | src/infrastructure/cli.py (1,289 líneas, 30+ commands) | Low: estable, bien documentado |
| **Entry Point** | ✅ Fixed | Líneas 1287-1289: `if __name__ == "__main__": app()` | Low: acaba de agregarse, funcional |
| **Daemon Support** | ❌ None | No hay soporte actual para procesos persistentes. | **HIGH**: LSP requiere persistencia |
| **IPC Strategy** | ✅ stdio (CLI → LSP) | LSP usa JSON-RPC sobre stdin/stdout. | Medium: sin heartbeat/watchdog |
| **Lock Mechanism** | ✅ fcntl | src/infrastructure/file_system_utils.py usa file_lock. | Low: existe, pero usage inconsistent |
| **Telemetry** | ✅ Local-first | src/infrastructure/telemetry.py (310 líneas), events.jsonl + metrics.json | Low: granular, rotado |

**Gap Crítico:** NO HAY soporte para daemons persistentes. LSP requiere arquitectura diferente.

---

## II. INTEGRACIÓN AST: SKELETON MAPS

### A. Punto de Integración Recomendado

```
src/infrastructure/ast_lsp.py (NUEVO MÓDULO)
├── SkeletonMapBuilder(tree_sitter)
│   ├── parse_python(file_path) → SkeletonMap
│   ├── parse_markdown(file_path) → SkeletonMap
│   └── compute_structural_hash() → sha256
├── SkeletonMapCache
│   ├── load_or_build(file_sha, structural_hash) → SkeletonMap
│   └── invalidate_if_changed() → bool
└── ASTRouter
    └── resolve_symbol(query, skeleton) → (file_path, line_no, kind)
```

**Se integra con:**
- `ContextService.search()` (línea 27+): antes de keyword search, intent classification.
- `SearchUseCase.execute()` (línea 44+): symbol-aware filtering.
- Telemetry: track `ast_parse_count`, `skeleton_hit_rate`, `resolve_latency_ms`.

### B. Tree-sitter: Decisión + Justificación

**Decisión:** Adoptar tree-sitter-python (native binding) para AST.

| Aspecto | Tree-sitter | Alternatives |
|--------|------------|--------------|
| **Overhead** | 0 (C bindings, ~2MB total) | Pyright: 150MB+, rope: 50MB+ |
| **Latency (cold)** | <50ms per file | Pyright: 2-5s per server start |
| **Latency (incremental)** | <1ms per edit | N/A (stateless) |
| **Error tolerance** | ✅ Parse incomplete code | ❌ Compiler-style (fail on error) |
| **Polyglot** | ✅ 30+ languages | ❌ Language-specific (rope=Python only) |

**Instalación:**
```bash
pip install tree-sitter tree-sitter-python
```

**Test Unitario Mínimo:**
```python
def test_skeleton_map_python():
    code = """
def foo(x: int) -> str:
    return str(x)
"""
    skeleton = SkeletonMapBuilder.parse_python(code)
    assert skeleton.functions[0].name == "foo"
    assert skeleton.functions[0].params == ["x: int"]
    assert skeleton.functions[0].lineno == 1
```

---

### C. Performance Targets y Limits

| Métrica | Target | Verificación |
|---------|--------|--------------|
| **Skeleton map size** | <10% of source | `len(skeleton.json) < len(source) * 0.1` |
| **Parse latency (single file)** | <50ms | `timeit(parse_python, 100)` < 50ms |
| **Full repo skeleton (5k files)** | <5s | `timeit(build_skeleton_index, 1)` < 5s |
| **Cache hit rate** | >85% | Track `skeleton_cache_hit / skeleton_cache_attempt` |

---

## III. INTEGRACIÓN LSP: HEADLESS CLIENT

### A. Decisión: Arquitectura con Demonio Persistente

**Problema:** Pyright/Pylance tarda 2-5s en cold-start. Tolerable una vez, inaceptable por query.

**Solución:** Daemon pattern con fallback.

```
┌─────────────────────┐
│   CLI Invocation    │
│ (ctx search ...)    │
└──────────┬──────────┘
           │
           ├─→ Check: LSP daemon running?
           │   ├─ YES → use LSP (hot)
           │   └─ NO  → start daemon (bg) + use Tree-sitter fallback (instant)
           │
           └─→ Return results
                (LSP will populate next invocation)
```

**Implementación:**

```python
# src/infrastructure/ast_lsp.py
class LSPDaemonManager:
    def __init__(self, segment_path: Path, language: str = "python"):
        self.daemon_pid_file = segment_path / "_ctx" / ".lsp_daemon.pid"
        self.language = language
        self.process: Optional[subprocess.Popen] = None
    
    def ensure_running(self) -> bool:
        """Start daemon if not already running. Return True if ready."""
        if self._is_running_and_responsive():
            return True
        
        self._start_daemon()
        # Don't block; LSP will be ready for next call
        return False
    
    def _start_daemon(self):
        """Start LSP server in background."""
        # Language-specific: pyright-langserver, pylance-langserver, etc.
        cmd = self._get_lsp_command()
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        # Save PID
        self.daemon_pid_file.write_text(str(self.process.pid))
```

**Riesgos Mitigados:**
1. **Cold start latency:** Fallback a Tree-sitter (instantáneo).
2. **Daemon divergence:** Revalidate con checksums en cada invocation.
3. **Zombie processes:** Implementar heartbeat + auto-restart.

---

### B. Servidor LSP por Lenguaje

| Lenguaje | Servidor Recomendado | Instalación | Notes |
|----------|---------------------|-------------|-------|
| **Python (P0)** | pyright-langserver | `pip install pyright` | Vendido con Pylance, determinista |
| **TS/JS (P2)** | typescript-language-server | `npm install typescript typescript-language-server` | Defer: no presentes en repo |
| **Markdown (P1)** | N/A (skeleton maps only) | Tree-sitter | No LSP maduro para MD |

**Decisión:** Python P0 con pyright-langserver.

---

### C. Set Mínimo de LSP Requests

Implementar SOLO esto (no todo el protocolo LSP):

| Request | Función | ROI | Esfuerzo |
|---------|---------|-----|----------|
| `textDocument/definition` | "Go to definition" | 🔴 High | Low |
| `textDocument/hover` | Type info + docstrings | 🔴 High | Low |
| `textDocument/references` | "Find all refs" | 🟡 Medium | Medium |
| `textDocument/publishDiagnostics` | Errors/warnings | 🟡 Medium | Low |
| `textDocument/documentSymbol` | File structure | 🟢 Low (Tree-sitter == this) | Medium |

**MVP:** definition + hover (2 requests).

---

### D. Virtual Document Handling (Shadow Workspace)

**Riesgo:** El agente genera código, lo quiere validar sin escribir en disk.

**Solución:** LSP didChange notifications.

```python
class ShadowWorkspace:
    """In-memory overlay of file edits, synced to LSP."""
    
    def __init__(self, lsp_client: LSPClient):
        self.overlays: dict[str, str] = {}  # file_path → edited_content
        self.lsp_client = lsp_client
    
    def propose_edit(self, file_path: str, new_content: str) -> DiagnosticsResult:
        """Apply edit to shadow, get LSP diagnostics, don't write disk."""
        self.overlays[file_path] = new_content
        
        # Notify LSP of change (without writing disk)
        self.lsp_client.send_did_change(file_path, new_content)
        
        # Get diagnostics
        diagnostics = self.lsp_client.get_diagnostics(file_path)
        
        return diagnostics
    
    def commit(self, file_path: str):
        """Write overlay to disk after validation passes."""
        Path(file_path).write_text(self.overlays[file_path])
        del self.overlays[file_path]
    
    def discard(self, file_path: str):
        """Rollback shadow edit."""
        del self.overlays[file_path]
        self.lsp_client.send_did_close(file_path)
```

---

## IV. PROGRESSIVE DISCLOSURE: CÓMO EXISTE HOY

### A. Niveles Actuales (Evidence-based)

En `src/application/context_service.py:90` (GetChunkUseCase):

```python
def execute(
    self,
    target_path: Path,
    ids: list[str],
    mode: Literal["raw", "excerpt", "skeleton"] = "excerpt",  # ← 3 MODES
    budget_token_est: int = 1500
) -> str:
```

| Modo | Descripción | Token Est. | Caso de Uso |
|------|-------------|-----------|-----------|
| `skeleton` | Solo firmas + doc | 100-300 | Exploración rápida |
| `excerpt` | Función completa | 500-1000 | Análisis moderado |
| `raw` | Archivo entero | 2000+ | Deep dive |

**Decisión existente:** Ya implementado 3 niveles. Extender con AST.

### B. Integration Point: AST-Aware Progressive Disclosure

Hoy: keyword search → archivos → lectura manual de niveles.  
Propuesto: skeleton search → símbolos → lectura inteligente.

```python
# NUEVO: src/application/context_service.py
def search_by_symbol(
    self, 
    symbol_name: str, 
    kind: Literal["function", "class", "module"] = None,
    disclosure_level: Literal["skeleton", "excerpt", "raw"] = "skeleton"
) -> SearchResult:
    """AST-aware search: find symbols, return at disclosure level."""
    
    # Step 1: Query skeleton maps
    skeleton_index = SkeletonMapCache.load_all(self.target_path)
    matching_symbols = skeleton_index.query(symbol_name, kind)
    
    # Step 2: Resolve to chunks with disclosure_level
    results = []
    for symbol in matching_symbols:
        chunk = self._get_chunk_at_disclosure(
            symbol.file_path,
            symbol.lineno,
            disclosure_level
        )
        results.append(SearchHit.from_chunk(chunk, symbol))
    
    return SearchResult(hits=results)
```

---

## V. CONCURRENCIA Y ESTADO

### A. Locks Existentes

| Recurso | Lock Type | Ubicación | Risk |
|---------|-----------|-----------|------|
| **context_pack.json** | fcntl (write) | file_system_utils.py | **MEDIUM**: No read lock → split-brain |
| **events.jsonl** | fcntl (append) | telemetry.py:145+ | Low: append-only, rotate handled |
| **session_<seg>.md** | None (append) | cli.py:session_append | **HIGH**: Concurrent appends can corrupt |
| **_ctx/telemetry/** | fcntl (per file) | telemetry.py:_flush_events | Medium: skip-if-busy → dropped events |

### B. Nuevos Locks Requeridos para AST+LSP

| Recurso | Proposed | Rationale |
|---------|----------|-----------|
| `.lsp_daemon.pid` | fcntl exclusive | Single daemon per segment |
| `skeleton_cache/` | fcntl read/write | Invalidation synchronization |
| `ast_probes.jsonl` | fcntl append | AST request log (telemetry) |

### C. Shadow Workspace Sync

**Riesgo:** Agent proposes edit → LSP sees it → agent rolls back → LSP stale.

**Mitigación:** Versioned overlays.

```python
class VersionedShadowWorkspace:
    def __init__(self, lsp_client):
        self.edits: dict[str, dict[int, str]] = {}  # file_path → {version: content}
        self.version_counter: dict[str, int] = {}
    
    def propose(self, file_path: str, content: str) -> int:
        """Return version ID."""
        if file_path not in self.version_counter:
            self.version_counter[file_path] = 0
        
        version = self.version_counter[file_path] + 1
        self.version_counter[file_path] = version
        self.edits[file_path][version] = content
        
        self.lsp_client.send_did_change(file_path, content, version)
        return version
    
    def rollback(self, file_path: str, version: int):
        """Return to version; LSP will invalidate newer."""
        if version in self.edits[file_path]:
            del self.edits[file_path][version]
            # Notify LSP to forget this version
```

---

## VI. CACHE E INVALIDACIÓN

### A. Cómo Se Obtienen Hashes Hoy

En `src/domain/context_models.py:SourceFile`:

```python
class SourceFile(BaseModel):
    path: str
    sha256: str      # ← File content hash
    mtime: float     # ← Modification time
    chars: int
```

Cálculo: `hashlib.sha256(file.read_bytes()).hexdigest()`

**Costo:** O(file_size) per check. Para 5k files ≈ 500ms.

### B. Structural Hash (AST-based)

**Propuesta:** En lugar de hashear el contenido, hashear el esqueleto.

```python
class StructuralHash:
    """Hash based on AST structure, not text."""
    
    @staticmethod
    def compute(skeleton_map: SkeletonMap) -> str:
        """Hash the structure, not the content."""
        # Extract signature-level info
        sig_parts = []
        for func in skeleton_map.functions:
            sig_parts.append(f"fn:{func.name}:{func.params}:{func.return_type}")
        for cls in skeleton_map.classes:
            sig_parts.append(f"cls:{cls.name}:{','.join(m.name for m in cls.methods)}")
        
        combined = "\n".join(sig_parts)
        return hashlib.sha256(combined.encode()).hexdigest()
```

**Ventaja:** If a function body changes pero la firma NO, structural_hash == old. No need to invalidate global index.

### C. Caché Mínima Viable

| Layer | Key | TTL | Size Limit | Hit Target |
|-------|-----|-----|-----------|-----------|
| **Skeleton map** | `file_sha + lang` | session (0) | 100MB (in-memory) | >85% |
| **Symbol index** | `repo_sha + lang` | 1 hour | 50MB | >90% |
| **LSP server state** | daemon_pid | persistent | ~200MB (LSP process) | N/A |
| **Diagnostics** | `(file_sha, overlay_version)` | 5 min | 10MB | >70% |

**Verificación de Caché:**
```python
def should_invalidate_skeleton(file_path: Path, cached_sha: str) -> bool:
    """Cheap check before re-parsing."""
    current_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return current_sha != cached_sha

def should_invalidate_index(repo_sha: str, cached_repo_sha: str) -> bool:
    """Check if repo changed since index was built."""
    # Compute repo_sha = hash of all skeleton maps
    return repo_sha != cached_repo_sha
```

---

## VII. SEGURIDAD Y LÍMITES

### A. Denylist Hard (No Ambigüedad)

| Path | Razón | Action |
|------|-------|--------|
| `.git/` | Leak internals | Skip (fail-closed) |
| `.env` | Secrets | NEVER parse with AST |
| `node_modules/` | Bloat | Skip |
| `__pycache__/` | Generated | Skip |
| `*.pyc, *.so` | Binaries | Skip (invalid UTF-8) |

**Implementation:**
```python
HARD_DENYLIST = {
    ".git", ".env", "node_modules", "__pycache__", ".venv", "venv"
}

def is_scannable(file_path: Path) -> bool:
    """Return False if in hard denylist."""
    for part in file_path.parts:
        if part in HARD_DENYLIST:
            return False
    return True
```

### B. Redaction en Logs

**Problema:** LSP diagnostics puede exponer código o paths sensibles.

**Mitigación:** Strip en telemetry events.

```python
REDACT_PATTERNS = [
    r"https?://[^/\s]+",      # URLs
    r"[A-Za-z0-9._%+-]+@[^@]+", # Emails
    r"(sk_|pk_)[a-zA-Z0-9]{32,}",  # API keys
]

def redact_for_telemetry(text: str) -> str:
    """Remove sensitive patterns."""
    for pattern in REDACT_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text
```

### C. Límites de Tamaño y Tiempo

| Límite | Valor | Verificación |
|--------|-------|--------------|
| Max file to parse | 1MB | `file_size > 1MB → skip + warn` |
| Max skeleton size | 10% of source | `len(skeleton.json) / len(source)` |
| Max LSP response time | 500ms | `timeout(lsp_request, 500ms) → fallback` |
| Max symbols per file | 1000 | `len(symbols) > 1000 → truncate + warn` |

---

## VIII. TESTS E INFRAESTRUCTURA

### A. Test Fixtures Requeridas

Ubicación: `tests/fixtures/ast_lsp/`

```
tests/fixtures/ast_lsp/
├── mini_repo/                  # Minimal valid Python repo
│   ├── simple.py              # 50 lines, 3 functions, 1 class
│   ├── nested/
│   │   └── module.py          # Nested imports
│   └── _ctx/
│       └── prime_mini.md       # Minimal context pack
├── broken_syntax.py            # Incomplete code (error recovery test)
├── large_file.py              # 10k+ lines (perf test)
└── lsp_server_mock.py         # Mock LSP server for CI
```

**Construcción:**
```python
# tests/conftest.py
@pytest.fixture
def mini_repo(tmp_path):
    """Create minimal valid repo for AST/LSP tests."""
    repo = tmp_path / "mini_repo"
    repo.mkdir()
    
    # Write files
    (repo / "simple.py").write_text("""
def add(x: int, y: int) -> int:
    return x + y

class Calculator:
    def multiply(self, x, y):
        return x * y
""")
    
    # Validate with FP Gate
    from src.infrastructure.validators import validate_segment_fp
    result = validate_segment_fp(repo)
    assert result.valid or result.errors  # Allow partial for fixture
    
    return repo
```

### B. Tests por Hito

#### Hito 1: AST Skeleton Map (Week 1)

```python
# tests/unit/test_ast_skeleton.py
def test_skeleton_map_python_functions(mini_repo):
    """Skeleton map captures function signatures."""
    skeleton = SkeletonMapBuilder.parse_python(
        mini_repo / "simple.py"
    )
    assert len(skeleton.functions) == 1
    assert skeleton.functions[0].name == "add"
    assert skeleton.functions[0].params == ["x: int", "y: int"]
    assert skeleton.functions[0].return_type == "int"

def test_skeleton_map_error_recovery():
    """Parse incomplete code gracefully."""
    broken = "def foo(\n  x: int\n    # missing closing paren"
    skeleton = SkeletonMapBuilder.parse_python(broken)
    # Should still recover the function signature
    assert len(skeleton.functions) >= 1

def test_structural_hash_stability():
    """Changing implementation doesn't change structure hash."""
    code1 = "def foo() -> int:\n    return 1"
    code2 = "def foo() -> int:\n    return 1 + 0"
    
    h1 = StructuralHash.compute(
        SkeletonMapBuilder.parse_python(code1)
    )
    h2 = StructuralHash.compute(
        SkeletonMapBuilder.parse_python(code2)
    )
    assert h1 == h2  # Same signature → same hash
```

#### Hito 2: LSP Client (Week 2)

```python
# tests/unit/test_lsp_client.py
@pytest.mark.integration
def test_lsp_definition_request(mini_repo):
    """Definition request works with mock server."""
    lsp_client = LSPClient(mini_repo, language="python")
    
    # Start mock server
    with mock_lsp_server(lsp_client):
        result = lsp_client.definition(
            file_path="simple.py",
            line=10,
            char=5
        )
        
        assert result.file_path == "simple.py"
        assert result.line >= 0

def test_lsp_daemon_lifecycle(mini_repo):
    """Daemon starts, stays warm, and cleans up."""
    manager = LSPDaemonManager(mini_repo)
    
    # First call: cold start
    ready = manager.ensure_running()
    assert ready is False
    
    # Second call: daemon running
    ready = manager.ensure_running()
    assert ready is True
    
    # Cleanup
    manager.stop()
    assert not manager._is_running_and_responsive()
```

#### Hito 3: Progressive Disclosure + Gates (Week 3)

```python
# tests/integration/test_ast_disclosure.py
def test_search_by_symbol_returns_skeleton(mini_repo):
    """Symbol search returns minimal context by default."""
    service = ContextService(mini_repo)
    result = service.search_by_symbol(
        "add",
        disclosure_level="skeleton"
    )
    
    # Skeleton = just signature
    hit = result.hits[0]
    assert "def add(x: int, y: int) -> int:" in hit.preview
    assert hit.token_est < 100

def test_search_by_symbol_disclosure_levels(mini_repo):
    """Disclosure levels return increasing detail."""
    service = ContextService(mini_repo)
    
    sk = service.search_by_symbol("add", disclosure_level="skeleton")
    ex = service.search_by_symbol("add", disclosure_level="excerpt")
    rw = service.search_by_symbol("add", disclosure_level="raw")
    
    assert sk.hits[0].token_est < ex.hits[0].token_est
    assert ex.hits[0].token_est < rw.hits[0].token_est
```

### C. Métricas y Observabilidad

Agregar a telemetry.py:

```python
# Nuevas métricas
METRICS_AST_LSP = {
    "ast_parse_count": 0,              # Cuántas veces parseamos
    "ast_parse_latency_ms": [],        # Distribución (p50, p95, max)
    "skeleton_cache_hit_count": 0,     # Caché hits
    "skeleton_cache_miss_count": 0,    # Caché misses
    "lsp_definition_count": 0,         # Definition requests sent
    "lsp_cold_start_ms": 0,            # Time to first LSP response
    "lsp_fallback_count": 0,           # Times we fell back to Tree-sitter
    "symbol_resolve_success_rate": 0,  # % of symbol queries resolved
    "bytes_read_per_task": 0,          # Efficiency metric
}
```

---

## IX. "WHAT WE MUST KNOW" - TABLA CRÍTICA

| # | Tema | Pregunta | Estado | Dónde Mirar | Cómo Verificar | Riesgo si No Se Resuelve |
|----|------|----------|--------|------------|---------------|-----------------------|
| **A1** | Lenguaje MVP | ¿Python first o multi-lang desde el inicio? | **KNOWN** | README.md, pyproject.toml | Grep `requires-python`, `src/` structure | Scope creep, Goldplating |
| **A2** | Prioridad lingüística | ¿TS/JS en Q1 o Q2? | **KNOWN** | docs/v2_roadmap/roadmap_v2.md | Line "AST/LSP" → Phase 3 (Month 1-2) | Deuda técnica, compatibilidad bifurcada |
| **B1** | Punto de integración AST | ¿Dónde vive `parse()` y `skeleton_build()`? | **UNKNOWN** | N/A (DESIGN NEEDED) | Crear `src/infrastructure/ast_lsp.py`, mock unit test | Código espagueti, acoplamiento |
| **B2** | Hooks en retrieval | ¿Dónde se enchufan los AST-aware selectors? | **PARTIALLY KNOWN** | src/application/context_service.py:27 (search method) | Add `search_by_symbol()`, integrate en SearchUseCase | Falsa precisión, no semantic |
| **B3** | Tree-sitter overhead | ¿Cuánto pesa? ¿Cuánto tarda el parse? | **UNKNOWN** | N/A (BENCHMARK NEEDED) | `pip install tree-sitter` → perf test en mini_repo | Sorpresas en prod, latencia |
| **B4** | Repo size target | ¿Qué tamaño de repo es realista? | **PARTIALLY KNOWN** | Audit anterior: "5k LOC min segment" | Build skeleton map en 5 different sizes, measure | OOM, timeouts |
| **C1** | LSP server choice (Python) | ¿Pyright o Pylance o rope? | **PARTIALLY KNOWN** | docs/research/lsp_ast_esqueleton.md | "pyright-langserver recomendado" | Incompatibilidad con diagn. |
| **C2** | Daemon lifecycle | ¿Cómo manejar cold start + crash recovery? | **UNKNOWN** | N/A (DESIGN NEEDED) | Spec "LSPDaemonManager" en ast_lsp.py | Stale server, memory leak |
| **C3** | Timeout/fallback strategy | ¿p95 cold start? ¿Fallback a Tree-sitter delay?| **UNKNOWN** | N/A (PERF NEEDED) | Benchmark: pyright start time + Tree-sitter parse time | Slow user experience |
| **D1** | Progressive disclosure actual | ¿Qué son skeleton/excerpt/raw hoy? | **KNOWN** | src/application/search_get_usecases.py:100 | Token budgets: 100-300 / 500-1000 / 2000+ | Desalineado con LSP |
| **D2** | Disclosure + AST integration | ¿Cómo se decide level automáticamente? | **UNKNOWN** | N/A (POLICY NEEDED) | Symbol search query → { skeleton if name_exact, excerpt if partial, raw if complex } | Manual tuning per query |
| **E1** | Locks existentes | ¿Qué se protege hoy con fcntl? | **KNOWN** | src/infrastructure/file_system_utils.py | context_pack.json (write), events.jsonl (append) | Race condition |
| **E2** | Shadow workspace sync | ¿Cómo LSP se entera de edits no-persisted? | **UNKNOWN** | N/A (PROTOCOL NEEDED) | Spec didChange versioning, test rollback | Stale diagnostics |
| **F1** | Repo SHA computation | ¿Cómo se calcula hoy? ¿Es rápido? | **PARTIALLY KNOWN** | src/domain/context_models.py:SourceFile | Manual hash per file, 500ms for 5k files | Slow invalidation |
| **F2** | Structural hash feasibility | ¿Vale la pena hashear esqueleto vs contenido? | **UNKNOWN** | N/A (PERF NEEDED) | Implement + benchmark: structural vs content hash | Overhead sin ROI |
| **F3** | Cache mínima viable | ¿Skeleton + symbol + LSP state? | **UNKNOWN** | N/A (DESIGN NEEDED) | Spec layers: in-mem skeleton, persistent symbol, LSP daemon | Memory thrashing |
| **G1** | Denylist existente | ¿Qué paths ya se ignoran? | **PARTIALLY KNOWN** | src/application/*.py for implicit filters | Grep ignore patterns, test with .env file | Secret leak |
| **G2** | Redaction for telemetry | ¿Qué patterns sensibles hay? | **UNKNOWN** | N/A (AUDIT NEEDED) | Scan 3 runs of `ctx search` output, log diagnostics → find secrets | Data leakage in logs |
| **G3** | Size/time limits | ¿Cuál es límite de file para parse? Timeout LSP? | **UNKNOWN** | N/A (POLICY NEEDED) | Spec: max 1MB file, 500ms LSP timeout | Denial of service |
| **H1** | Test fixtures | ¿Existe mini_repo o e2e? | **PARTIALLY KNOWN** | tests/fixtures/ (empty) | Create `mini_repo` fixture en conftest.py | Brittle tests |
| **H2** | CI strategy | ¿Cómo correr LSP en CI sin GUI? | **UNKNOWN** | .github/workflows/ (not visible) | Mock LSP server or headless pyright | Flaky CI |
| **H3** | Metrics baseline | ¿Cuáles son métricas hoy para AST/LSP? | **UNKNOWN** | src/infrastructure/telemetry.py | NONE exist yet → Add AST_PARSE_MS, SKELETON_CACHE_HIT, etc. | No observability |

---

## X. DECISIONES RECOMENDADAS (Lean)

### 1. **Lenguaje Objetivo: Python FIRST, TS DEFERRED**

**Opciones:**
- A: Python solo en MVP
- B: Python + TS/JS desde day 1
- C: TS/JS first (SDK-first)

**Recomendación: A (Python first)**

| Aspecto | A (Python) | B (Multi) | C (TS first) |
|---------|-----------|----------|-------------|
| Effort | 3 days | 2 weeks | 2 weeks |
| Alignment | 🔴 100% (Python repo) | 🟡 50% (futuro) | 🔵 0% (no TS hoy) |
| Risk | Low | Medium (tools async) | High (no baseline) |

**Trade-off:** Agregar TS after v1.0 is cheaper que startegic paralysis.

---

### 2. **Estrategia LSP: Demonio Persistente + Fallback Inmediato**

**Opciones:**
- A: Always use LSP (slow cold start)
- B: Always use Tree-sitter (no semantics)
- C: Daemon warm + instant fallback

**Recomendación: C**

```
Invocation 1: [Cold] → Fallback (instant, Tree-sitter) + Start daemon (bg)
Invocation 2: [Hot] → LSP (low latency, semantics)
```

**Metrics:**
- Invocation 1: ~50ms (Tree-sitter)
- Invocation 2+: ~100ms (LSP warm)

---

### 3. **Punto de Integración: Nuevo `src/infrastructure/ast_lsp.py`**

**Ubicación:** Nuevo módulo, no mezclar con `context_service.py`.

**Responsabilidades:**
- SkeletonMapBuilder (parse + cache)
- LSPDaemonManager (lifecycle + IPC)
- ASTRouter (symbol resolution)

**Integración mínima:** Agregar `search_by_symbol()` a `ContextService`, call desde `SearchUseCase`.

---

### 4. **Tree-sitter: Adoptar, No Inventar**

**Decisión:** `pip install tree-sitter tree-sitter-python`.

**NO hacer:**
- Regex-based parsing (fragile, nested structures)
- Full AST serialization (overkill)
- Incremental parsing v1 (premature optimization)

---

### 5. **Shadow Workspace: Versioned Overlays**

**Decisión:** Edits no-persisted via LSP didChange con versioning.

**Mecanismo:**
1. Agent proposes → version_id = N
2. LSP validates → diagnostics
3. If pass → write disk; if fail → rollback (forget v=N)

---

### 6. **Cache Minimal: 3 Layers**

| Layer | Key | TTL | Size |
|-------|-----|-----|------|
| **In-mem skeleton** | file_sha + lang | Session | 100MB |
| **Persistent symbol index** | repo_sha | 1h | 50MB |
| **LSP daemon state** | pid + lang | Persistent | 200MB |

---

### 7. **Progressive Disclosure: Heuristic Default**

**Regla:** Si symbol search exacto → skeleton. Si partial/fuzzy → excerpt. Si multiple matches → raw.

```python
def infer_disclosure_level(
    num_matches: int,
    match_type: Literal["exact", "partial", "fuzzy"]
) -> Literal["skeleton", "excerpt", "raw"]:
    if match_type == "exact":
        return "skeleton"
    elif match_type == "partial" or num_matches <= 3:
        return "excerpt"
    else:
        return "raw"
```

---

### 8. **Denylist: Hard + Explicit**

**Hard:**
```python
{".git", ".env", "node_modules", "__pycache__", ".venv", "venv", "*.pyc"}
```

**Soft** (warn, don't skip):
```python
{".github", "build/", "dist/", "*.egg-info"}
```

---

### 9. **Timeouts: p95-based, Not Conservative**

| Operation | Target p95 | Fallback | Action |
|-----------|-----------|----------|--------|
| Parse (single file) | 50ms | N/A | Skip if > 100ms |
| Skeleton build (repo) | 5s | N/A | Async + cache |
| LSP definition | 100ms | Tree-sitter scope query | Fallback |
| LSP hover | 100ms | Docstring from source | Fallback |

---

### 10. **Testing: Fixtures + Mock Server**

**MVP tests:**
- ✅ Skeleton parsing (functions, classes, signatures)
- ✅ Structural hash stability
- ✅ LSP mock server (textDocument/definition)
- ✅ Daemon lifecycle
- ✅ Shadow workspace versioning
- ✅ Progressive disclosure inference
- ✅ Denylist enforcement

**Integration tests (post-MVP):**
- Real LSP server in CI
- Large repo performance
- Daemon crash recovery

---

## XI. MVP PLAN (3 HITOS)

### Hito 1: AST Skeleton Map (4 días)

**Objetivo:** Tree-sitter parsing + caching works, skeleton maps reduce 100:1.

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: SkeletonMapBuilder class
2. `tests/fixtures/ast_lsp/mini_repo/`: Test fixture
3. 10 unit tests (parsing, error recovery, hash stability)
4. Benchmark: parse 5k files in <5s

**DoD:**
- [ ] Parse Python code with Tree-sitter
- [ ] Extract functions, classes, signatures
- [ ] Structural hash computed and stable
- [ ] Cache implementation (file_sha-keyed)
- [ ] 85%+ unit test coverage
- [ ] Skeleton maps 100:1 size reduction verified

**Tests (specific):**
```
test_skeleton_map_python_functions
test_skeleton_map_python_classes
test_skeleton_map_error_recovery
test_structural_hash_stability
test_structural_hash_change_with_new_function
test_cache_hit_on_unmodified_file
test_cache_miss_on_content_change
test_cache_miss_on_structural_change
test_skeleton_size_reduction_100_to_1
test_bench_parse_5k_files_under_5s
```

**Rollback Plan:**
- If Tree-sitter overhead > 100ms per file: Use regex fallback (lower precision).
- If cache thrashing: Reduce TTL to session-only (0 persistence).

---

### Hito 2: LSP Headless Client (5 días)

**Objetivo:** Daemon warm + fallback instant. textDocument/definition y hover working.

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: LSPDaemonManager class
2. `src/infrastructure/ast_lsp.py`: LSPClient (JSON-RPC wrapper)
3. `tests/unit/test_lsp_client.py`: 8 unit tests + mock server
4. ShadowWorkspace class with versioning

**DoD:**
- [ ] LSP daemon starts in background
- [ ] Daemon lifecycle: start, ensure_running, stop, crash recovery
- [ ] JSON-RPC textDocument/definition request/response
- [ ] JSON-RPC textDocument/hover working
- [ ] Shadow workspace overlays (didChange, versions)
- [ ] Fallback to Tree-sitter if LSP cold/unavailable
- [ ] Telemetry: lsp_cold_start_ms, lsp_fallback_count
- [ ] 80%+ test coverage

**Tests (specific):**
```
test_lsp_daemon_starts_background
test_lsp_daemon_ensure_running_idempotent
test_lsp_definition_request_basic
test_lsp_hover_request_basic
test_lsp_daemon_crash_recovery
test_lsp_cold_start_fallback_instant
test_shadow_workspace_propose_edit_get_diagnostics
test_shadow_workspace_commit_writes_disk
test_shadow_workspace_rollback_forgets_version
test_shadow_workspace_version_increment
test_lsp_timeout_fallback_to_treesitter
test_lsp_daemon_cleanup_on_exit
```

**Rollback Plan:**
- If LSP cold start > 2s: Move to "start-on-segment-init" daemon pool (persistent).
- If IPC overhead > 50ms per request: Cache LSP responses in skeleton map.

---

### Hito 3: Progressive Disclosure + Integration (4 días)

**Objetivo:** `search_by_symbol()` ready, disclosure levels inferred correctly, end-to-end tested.

**Deliverables:**
1. `src/application/context_service.py`: `search_by_symbol()` method
2. `src/application/search_get_usecases.py`: SymbolSearchUseCase
3. `src/infrastructure/cli.py`: New command `ctx search-symbol --name <symbol>`
4. Integration tests: 6 tests
5. Telemetry: skeleton_cache_hit_rate, symbol_resolve_success_rate, bytes_read_per_task

**DoD:**
- [ ] Symbol search finds function, class, module by name
- [ ] Disclosure level inferred from match type (exact → skeleton, partial → excerpt, etc.)
- [ ] Progressive Disclosure: skeleton < excerpt < raw (token-wise)
- [ ] Telemetry: track symbol resolution accuracy
- [ ] No breaking changes to existing ctx commands
- [ ] 75%+ integration test coverage
- [ ] CLI `ctx search-symbol` user-testable

**Tests (specific):**
```
test_search_by_symbol_exact_match_returns_skeleton
test_search_by_symbol_partial_match_returns_excerpt
test_search_by_symbol_multiple_matches_return_raw
test_search_by_symbol_disclosure_levels_increasing_detail
test_search_by_symbol_respects_denylist
test_search_by_symbol_telemetry_records_accuracy
test_cli_search_symbol_command_works
test_progressive_disclosure_token_budgets_respected
test_integration_full_pipeline_query_to_result
```

**Rollback Plan:**
- If disclosure level inference too noisy: Make it explicit CLI param (`--disclosure skeleton|excerpt|raw`).
- If symbol resolution success < 70%: Require user to specify kind (`--kind function|class|module`).

---

## XII. ANTI-PATRONES A EVITAR (Top 7)

### 1. ❌ "Indexar todo el código en memory"
**Aplicado a Trifecta:** NO construir AST global de 5k archivos upfront.  
**Si:** Skeleton maps lazy-loaded, LRU cache, persistent index.

### 2. ❌ "Fallback a regex si LSP slow"
**Problema:** Regex no maneja anidación → false negatives.  
**Si:** Fallback a Tree-sitter (siempre disponible, robusto).

### 3. ❌ "Shadow workspace sin versionado"
**Problema:** Agent proposes → LSP sees it → agent rolls back → LSP stale.  
**Si:** Version per edit, explicit commit/rollback, LSP notified.

### 4. ❌ "Usar mtime para cache invalidation"
**Problema:** File regenerated en <1s → mtime == old → stale cache.  
**Si:** Content hash + structural hash (content mismatch → invalidate global index).

### 5. ❌ "Esperar a que LSP esté listo"
**Problema:** Cold start 2-5s → CLI timeout esperando.  
**Si:** Instant fallback (Tree-sitter) + daemon warm para next call.

### 6. ❌ "Proteger todo con locks"
**Problema:** Deadlock, contención, complexity.  
**Si:** Minimal locks (context_pack.json, .lsp_daemon.pid), append-only (logs).

### 7. ❌ "Redactar secrets en LSP requests"
**Problema:** .env file roto, LSP emite "variable no found", secret logged.  
**Si:** Hard denylist (.env), redact patterns en telemetry, scan before parsing.

---

## XIII. MATRIZ DE RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación | Dueño |
|--------|--------------|---------|-----------|--------|
| **LSP daemon cold start >2s** | HIGH | MEDIUM | Fallback tree-sitter instant, daemon bg | Hito 2 |
| **Shadow workspace sync drift** | MEDIUM | HIGH | Version per edit, explicit rollback | Hito 2 |
| **Tree-sitter parse fails** | LOW | MEDIUM | Error recovery (parse rest of file) | Hito 1 |
| **Memory leak in LSP daemon** | LOW | HIGH | Heartbeat + auto-restart, resource limits | Hito 2 |
| **Split-brain in context_pack.json** | MEDIUM | HIGH | fcntl read lock + version bump | Pre-sprint |
| **Secret leak in diagnostics** | LOW | CRITICAL | Hard denylist + redaction patterns | Hito 3 |
| **Skeleton cache thrashing** | MEDIUM | LOW | Session-only TTL, lazy-load | Hito 1 |
| **Timeout LSP → user frustration** | MEDIUM | MEDIUM | p95-based timeout, clear fallback message | Hito 2 |
| **Test brittleness (LSP mocking)** | HIGH | MEDIUM | Mock server in tests, no real LSP in CI | Hito 2 |
| **Perf regression (5k files)** | MEDIUM | MEDIUM | Async skeleton build, cache, benchmarks | Hito 1 |

---

## XIV. CHECKLIST PRE-SPRINT

- [ ] **Decision Log:** 3 decisiones críticas documentadas y aprobadas.
- [ ] **Risk Register:** 10 riesgos con mitigaciones claras.
- [ ] **Fixture Setup:** mini_repo creado y validado.
- [ ] **Mock LSP Server:** Implementado o identificado (multilspy ref).
- [ ] **Telemetry Extended:** Nuevas métricas AST/LSP mapeadas.
- [ ] **Lock Audit:** Revisión de fcntl usage actual vs requerido.
- [ ] **Denylist Audit:** Scan de código para patterns sensibles.
- [ ] **Performance Baseline:** Benchmark inicial (Tree-sitter, pyright cold start).
- [ ] **CLI Stub:** `ctx search-symbol` scaffolded (no impl).
- [ ] **Rollback Plan:** Por hito, con alternativas claras.

---

## CONCLUSIÓN

La implementación de AST+LSP en Trifecta es **viable y urgente** para habilitar symbol-aware context selection. El documento identifica **3 decisiones críticas** (Python first, demonio + fallback, nuevo módulo ast_lsp.py), **3 unknowns peligrosos** (LSP binary install, shadow sync, cache metrics), y proporciona un **MVP plan de 13 días** con rollback claros.

**Recomendación:** Proceder al sprint con Hito 1 (AST skeleton maps) inmediatamente. Este hito desbloquea todos los demás y tiene bajo riesgo.

---

**Auditor:** GitHub Copilot (Preparación Técnica)  
**Fecha de Completitud:** 2026-01-01  
**Próxima Revisión:** Post-Hito 1 (4 días)
