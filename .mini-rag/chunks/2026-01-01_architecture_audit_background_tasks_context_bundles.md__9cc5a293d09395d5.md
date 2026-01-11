#### 3.3.3 Comandos CLI Nuevos

```bash
# Habilitar AST capture (una vez)
export TRIFECTA_BUNDLE_CAPTURE_AST=1

# Run con AST events
trifecta ctx build --segment . --bundle-capture

# Inspeccionar bundle con AST events
trifecta bundle show run_xyz --include-ast
# Output: [muestra LSP tool calls]

# Replay sin AST (mock)
trifecta bundle replay run_xyz --skip-ast
```
