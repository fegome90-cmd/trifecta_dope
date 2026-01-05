### Bloqueador #1: PATH HYGIENE (CRÍTICO)

**Archivos a tocar:**
1. `src/application/use_cases.py` - DONDE escribe el pack con rutas absolutas
2. `tests/integration/test_path_hygiene.py` - NUEVO test tripwire

**DoD:**
- [ ] `context_pack.json` NO contiene `/Users/` o `/home/` después de `ctx sync`
- [ ] Test tripwire detecta rutas absolutas y falla
- [ ] Chunks con rutas absolutas se sanitizan en write-time

**Test Tripwire:**
```python
# tests/integration/test_path_hygiene.py
def test_context_pack_no_absolute_paths(tmp_path):
    """FAIL if any absolute path leaks into context_pack.json or chunks."""
    # Run ctx sync
    # Load context_pack.json
    # Assert no /Users/ or /home/ in any field
```

**Comandos de verificación:**
```bash
# 1. Sync para generar pack
uv run trifecta ctx sync -s .

# 2. Verificar NO hay paths absolutos
grep -E '"/Users/|"/home/' _ctx/context_pack.json
# Expected: NO OUTPUT (exit code 1)

# 3. Verificar test pasa
uv run pytest tests/integration/test_path_hygiene.py -v
# Expected: PASSED
```

---
