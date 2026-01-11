### Para G2 (path hygiene):
```bash
# Encontrar writer de context_pack
rg -n "context_pack|ContextPack|write_.*pack|json.*pack" src/

# Inspeccionar campos de path
rg -n "repo_root|source_files|path|abs|resolve\(" src/

# Verificar uso de AtomicWriter
rg -n "AtomicWriter|model_dump_json|sanitized_dump" src/

# Test tripwire: sync + grep con RC preservado
uv run trifecta ctx sync -s . >/dev/null 2>&1 && rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json; echo "RC=$? (1=PASS)"
```
