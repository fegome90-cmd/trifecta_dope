# Micro-Audit Report (v1)

**commit**: bb615dfdc3ce62b5139d1f27fa8f376b21dd5b09  
**date**: 2026-01-02  
**environment**: ripgrep 15.1.0, Python 3.13.7, macOS

---

## Top 10 Hallazgos (ordenados por ROI)

### [P0] 1. Stringly-typed PrimeFileNotFoundError Classification

- **Señal (command)**: `rg 'in str\(e\)|"Expected .* not found"' src tests`
- **Ubicación**: `src/infrastructure/cli.py:992`, `tests/unit/test_type_priority.py:23,28`
- **Riesgo**: Error classification uses substring matching (`"Expected prime file not found" in str(e)`). Refactoring the error message breaks the error card routing silently. CI passes but wrong error is shown to user.
- **Fix lean** (<= 60 líneas):
  ```python
  # Replace string matching with type check:
  except PrimeFileNotFoundError as e:
      return render_error_card("SEGMENT_NOT_INITIALIZED", ...)
  except FileNotFoundError as e:  # Generic fallback
      ...
  ```
  Remove the `TRIFECTA_DEPRECATED: fallback_prime_missing_string_match_used` path once type-based routing is 100%.
- **Tripwire test**: `test_error_classification_by_type_not_string`
  ```python
  def test_error_classification_by_type_not_string():
      # Raise PrimeFileNotFoundError with a DIFFERENT message
      # Assert error card code is still SEGMENT_NOT_INITIALIZED
  ```
- **Evidencia requerida**: `pytest tests/unit/test_type_priority.py -v`

---

### [P0] 2. LSP Daemon `time.sleep` Flakes in Integration Tests

- **Señal (command)**: `rg 'time\.sleep' tests`
- **Ubicación**: `tests/integration/test_lsp_daemon.py:52,89,146,150,178,221,242,262,324,328,362`
- **Riesgo**: 11 `time.sleep()` calls (up to 3.5s) make daemon tests flaky on slow CI runners. False green when sleep is too short, false red on slow machines.
- **Fix lean** (<= 60 líneas):
  ```python
  # Replace time.sleep with Event-based wait
  def wait_for_condition(predicate, timeout=5.0, poll=0.05):
      deadline = time.monotonic() + timeout
      while time.monotonic() < deadline:
          if predicate():
              return True
          time.sleep(poll)
      return False
  ```
  Apply to daemon ready, lock acquisition, TTL expiry checks.
- **Tripwire test**: `test_daemon_ready_uses_event_not_sleep`
  ```python
  def test_daemon_ready_uses_event_not_sleep(monkeypatch):
      sleep_calls = []
      monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))
      # ... start daemon, wait for ready ...
      assert all(s <= 0.1 for s in sleep_calls), "No long sleeps allowed"
  ```
- **Evidencia requerida**: `pytest tests/integration/test_lsp_daemon.py -v --tb=short`

---

### [P1] 3. Excessive `pytest.skip()` in Acceptance Tests

- **Señal (command)**: `rg 'pytest\.skip' tests`
- **Ubicación**: `tests/acceptance/test_pd_evidence_stop_e2e.py:48,58,71,80,176,187,271,368,379`
- **Riesgo**: 9 conditional skips in one acceptance test file. Tests can pass in CI without actually exercising the happy path. "Verde falso."
- **Fix lean** (<= 60 líneas):
  1. Create a `@pytest.fixture` that sets up a known-good segment with `trifecta create`.
  2. Replace conditional skips with `pytest.fail()` when preconditions not met.
  3. Mark truly environment-dependent tests with `@pytest.mark.slow`.
- **Tripwire test**: `test_no_skip_in_acceptance_tests`
  ```python
  def test_no_skip_in_acceptance_tests():
      import ast
      for f in Path("tests/acceptance").glob("*.py"):
          tree = ast.parse(f.read_text())
          skips = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and getattr(n.func, "attr", "") == "skip"]
          assert len(skips) == 0, f"Remove pytest.skip from {f}"
  ```
- **Evidencia requerida**: `pytest tests/acceptance/ -v --tb=short`

---

### [P1] 4. CWD Coupling in Integration Tests

- **Señal (command)**: `rg 'Path\.cwd\(\)' tests`
- **Ubicación**: `tests/integration/test_lsp_daemon.py:23`, `tests/integration/test_lsp_telemetry.py:12,60,71,104,118`
- **Riesgo**: Tests use `Path.cwd()` instead of `tmp_path` fixture. Running tests from different directory or in parallel can cause cross-contamination.
- **Fix lean** (<= 60 líneas):
  ```python
  # Before:
  root = Path.cwd()
  # After:
  root = tmp_path
  ```
  Update 6 test files to accept `tmp_path` fixture and create isolated segments.
- **Tripwire test**: `test_no_cwd_in_tests`
  ```python
  def test_no_cwd_in_tests():
      for f in Path("tests").rglob("*.py"):
          content = f.read_text()
          assert "Path.cwd()" not in content or "tmp_path" in content
  ```
- **Evidencia requerida**: `rg 'Path\.cwd' tests --count`

---

### [P1] 5. LSP Client Shutdown Race Condition

- **Señal (command)**: `rg 'join\(|terminate\(|BrokenPipeError' src`
- **Ubicación**: `src/infrastructure/lsp_client.py:142-154`
- **Riesgo**: Shutdown sequence does `terminate()` -> `wait()` -> `thread.join()` -> close streams. If thread is still reading when streams close, `BrokenPipeError` or `ValueError: I/O operation on closed file` can occur.
- **Fix lean** (<= 60 líneas):
  ```python
  # Current: terminate -> wait -> join -> close
  # Fixed:
  self._stopping.set()  # Signal stop first
  self._thread.join(timeout=1.0)  # Let thread exit cleanly
  if self._thread.is_alive():  # Thread still alive, force kill
      self.process.terminate()
      self.process.wait(timeout=0.5)
  # Only close streams AFTER thread is dead
  self.stdin.close()
  self.stdout.close()
  ```
- **Tripwire test**: `test_shutdown_no_broken_pipe`
  ```python
  def test_shutdown_no_broken_pipe(capfd):
      client = LSPClient(...)
      client.shutdown()
      captured = capfd.readouterr()
      assert "BrokenPipeError" not in captured.err
      assert "I/O operation on closed file" not in captured.err
  ```
- **Evidencia requerida**: `pytest tests/integration/test_lsp_no_stderr_errors.py -v`

---

### [P1] 6. Missing Precedence Documentation for TRIFECTA_* Env Vars

- **Señal (command)**: `rg 'TRIFECTA_' src`
- **Ubicación**: `src/infrastructure/cli.py:69,343,354`, `src/infrastructure/deprecations.py:33`
- **Riesgo**: 4 env vars exist but no single source of truth documents the default → env → flag precedence. Agents and users may set conflicting values.
- **Fix lean** (<= 60 líneas):
  Create `docs/ENV_VARS.md` with precedence table (see below). Add docstring to CLI functions referencing it.
- **Tripwire test**: `test_env_var_precedence_documented`
  ```python
  def test_env_var_precedence_documented():
      doc = Path("docs/ENV_VARS.md").read_text()
      for var in ["TRIFECTA_TELEMETRY_LEVEL", "TRIFECTA_PD_MAX_CHUNKS",
                  "TRIFECTA_PD_STOP_ON_EVIDENCE", "TRIFECTA_DEPRECATED"]:
          assert var in doc
  ```
- **Evidencia requerida**: `cat docs/ENV_VARS.md`

---

### [P2] 7. Stringly-typed Chunk ID Parsing

- **Señal (command)**: `rg 'startswith\(|split\(' src/application`
- **Ubicación**: `src/application/context_service.py:28-29`, `src/application/use_cases.py:849-857`
- **Riesgo**: Chunk IDs parsed via `split(":", 1)` and `startswith("skill:")`. Adding new chunk types requires changes in multiple files.
- **Fix lean** (<= 60 líneas):
  Create `ChunkId` dataclass with `.kind` and `.name` properties:
  ```python
  @dataclass
  class ChunkId:
      kind: str  # "skill", "prime", "doc", etc.
      name: str

      @classmethod
      def parse(cls, raw: str) -> "ChunkId":
          parts = raw.split(":", 1)
          return cls(kind=parts[0].lower(), name=parts[1] if len(parts) > 1 else "")
  ```
- **Tripwire test**: `test_chunk_id_parse_exhaustive` (already exists in `tests/unit/test_chunk_id_parse.py`)
- **Evidencia requerida**: `pytest tests/unit/test_chunk_id_parse.py -v`

---

### [P2] 8. Segment Resolution via `resolve()` Everywhere

- **Señal (command)**: `rg 'resolve\(\)' src/infrastructure`
- **Ubicación**: `src/infrastructure/cli.py` (15 occurrences), `src/infrastructure/segment_utils.py:13-36`
- **Riesgo**: `Path.resolve()` called on nearly every CLI command entry. Symlinks may resolve unexpectedly. No central "resolved once, pass around" pattern.
- **Fix lean** (<= 60 líneas):
  Create `ResolvedSegment` newtype wrapper that guarantees resolution happened once:
  ```python
  class ResolvedSegment(Path):
      """A segment path that has been resolved exactly once."""
      @classmethod
      def from_raw(cls, raw: str) -> "ResolvedSegment":
          return cls(Path(raw).resolve())
  ```
  Update CLI handlers to accept `ResolvedSegment`.
- **Tripwire test**: `test_resolved_segment_is_absolute`
- **Evidencia requerida**: `rg 'resolve\(\)' src/infrastructure --count`

---

### [P2] 9. Hardcoded `_ctx/` Path Literals

- **Señal (command)**: `rg '_ctx/' src`
- **Ubicación**: 30+ locations across `cli.py`, `validators.py`, `templates.py`, `use_cases.py`
- **Riesgo**: Context directory hardcoded as `_ctx/`. Renaming requires a mass find-replace.
- **Fix lean** (<= 60 líneas):
  Define `CTX_DIR = "_ctx"` constant in `src/domain/constants.py`. Replace all string literals.
- **Tripwire test**: `test_no_hardcoded_ctx_literals`
  ```python
  def test_no_hardcoded_ctx_literals():
      for f in Path("src").rglob("*.py"):
          if "constants.py" in str(f):
              continue
          assert '"_ctx/' not in f.read_text(), f"Use CTX_DIR constant in {f}"
  ```
- **Evidencia requerida**: `rg '"_ctx/' src --count`

---

### [P2] 10. Lower-case String Comparisons Scattered

- **Señal (command)**: `rg 'lower\(\)' src/application`
- **Ubicación**: `context_service.py` (8 occurrences), `use_cases.py` (5), `plan_use_case.py` (9)
- **Riesgo**: Case-insensitive comparisons done via `.lower()` ad-hoc. Locale issues possible, no central normalization.
- **Fix lean** (<= 60 líneas):
  Create `normalize_query(q: str) -> str` helper that does `.lower().strip()` once.
  Already partially exists in `query_normalizer.py` but not used everywhere.
- **Tripwire test**: `test_query_normalizer_used_for_search`
- **Evidencia requerida**: `pytest tests/unit/test_query_normalizer.py -v`

---

## Tabla de precedencia detectada (TRIFECTA_*)

| Setting | Default | Env Var | CLI Flag | Conflictos detectados |
|---------|---------|---------|----------|----------------------|
| Telemetry Level | `"lite"` | `TRIFECTA_TELEMETRY_LEVEL` | `--telemetry` | ❌ Env wins over default, flag wins over env. **No conflict.** |
| PD Max Chunks | `None` (unlimited) | `TRIFECTA_PD_MAX_CHUNKS` | `--max-chunks` | ⚠️ Flag overrides env. Test exists in `test_pd_env_var.py`. |
| PD Stop on Evidence | `False` | `TRIFECTA_PD_STOP_ON_EVIDENCE` | `--stop-on-evidence` | ⚠️ Env only checked if flag not provided. |
| Deprecated Policy | `"off"` | `TRIFECTA_DEPRECATED` | N/A | ✅ Env-only, no flag. Tests in `test_deprecations_policy.py`. |

**Conflictos**:
- `TRIFECTA_PD_STOP_ON_EVIDENCE` parsing uses `str.lower() == "true"` — could fail for `"1"` or `"yes"`.
- `TRIFECTA_PD_MAX_CHUNKS` does `int()` with no error handling for non-numeric values.

---

## Lista de tests con SKIP/XFAIL

| File | Skip/XFail Count | Reason | Propuesta de reemplazo |
|------|-----------------|--------|----------------------|
| `test_pd_evidence_stop_e2e.py` | 9 `pytest.skip()` | Precondition failures | Use fail-closed fixture with known-good segment |
| `test_segment_id_invariants.py` | 2 `pytest.skip()` | No events.jsonl | Create fixture that generates telemetry |
| `test_prime_tripwires.py` | 2 `pytest.skip()` | Prime file missing | Include in segment creation fixture |
| `test_prime_paths_only.py` | 1 `pytest.skip()` | Prime file not found | Same as above |
| `test_prime_top10_in_pack.py` | 1 `pytest.skip()` | Prime file missing | Same as above |
| `test_plan_use_case.py` | 1 `pytest.skip()` | `_ctx/generated/` missing | Create in fixture or use `tmp_path` |
| `test_cli_smoke_real_use.py` | 1 `@pytest.mark.skip` | Parallel execution | Convert to proper parametrization |

**Total**: 17 skip sites across 7 files.

---

## Top 3 Micro-Tasks (mayor ahorro de horas en próximo sprint)

### 🥇 1. Error Classification by Type (P0 #1)
**Ahorro esperado**: 4-6 hours/sprint in debugging "wrong error card shown"  
**Esfuerzo**: 30 min  
**Riesgo si no se hace**: Silent regression breaks agent error handling

```bash
# Commands to implement
# 1. Update cli.py to catch PrimeFileNotFoundError by type
# 2. Add tripwire test
# 3. Remove fallback_prime_missing_string_match_used deprecation path
```

---

### 🥈 2. Replace `time.sleep` with Event-based Wait (P0 #2)
**Ahorro esperado**: 2-3 hours/sprint in flaky test retries  
**Esfuerzo**: 1 hour  
**Riesgo si no se hace**: CI flakes block deployments

```bash
# 1. Create tests/conftest.py::wait_for_condition helper
# 2. Apply to test_lsp_daemon.py (11 sites)
# 3. Add tripwire test
```

---

### 🥉 3. Create ENV_VARS.md Precedence Table (P1 #6)
**Ahorro esperado**: 1-2 hours/sprint in "why isn't my env var working" support  
**Esfuerzo**: 20 min  
**Riesgo si no se hace**: Agents set conflicting env vars, confusing debug sessions

```bash
# 1. Create docs/ENV_VARS.md with table from this report
# 2. Add tripwire test
# 3. Reference in CLI help strings
```

---

## Apéndice: Comandos de Escaneo Ejecutados

```bash
# A) Stringly-typed parsing
rg -n --hidden --glob '!**/.venv/**' --glob '!**/_ctx/**' \
  'startswith\(|endswith\(|in error_msg|in str\(e\)|"Expected .* not found"|contains\(|split\(|lower\(\)' \
  src tests

# B) CWD / paths relativos
rg -n --hidden --glob '!**/.venv/**' --glob '!**/_ctx/**' \
  'Path\.cwd\(\)|os\.getcwd\(\)|chdir\(|\b\./_ctx\b|_ctx/|relative_to\(|resolve\(\)' \
  src tests scripts

# C) Tests flakey
rg -n --hidden --glob '!**/.venv/**' \
  '@pytest\.mark\.skip|pytest\.skip|xfail|flaky|random|time\.sleep|depends on|local only|CI' \
  tests

# D) Flags/env
rg -n --hidden --glob '!**/.venv/**' \
  'os\.environ|getenv\(|TRIFECTA_|--[a-z0-9_-]+' \
  src tests

# E) Concurrencia / shutdown
rg -n --hidden --glob '!**/.venv/**' \
  'threading\.Thread|daemon=True|join\(|terminate\(|kill\(|wait\(|BrokenPipeError|write to closed file|ValueError: I/O operation on closed file|OSError' \
  src tests
```
