### E1: Path Hygiene Verificado
```bash
$ uv run trifecta ctx sync -s .
[output completo]

$ grep -E '"/Users/|"/home/' _ctx/context_pack.json
# Expected: NO OUTPUT (exit code 1)

$ uv run pytest tests/integration/test_path_hygiene.py -v
# Expected: test_no_absolute_paths PASSED
```
