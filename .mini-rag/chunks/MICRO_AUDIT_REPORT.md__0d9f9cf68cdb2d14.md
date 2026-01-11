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
