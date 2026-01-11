### Opción A: Comando Prefijo (RECOMENDADO)
```
Observability: lsp.*, ast.*, ctx.*, telemetry.*
Session:       session.*
```

**Ventaja**: Fácil filtrar por prefijo
```bash
# Solo observability
grep -E '"cmd": "(lsp|ast|ctx)\.' events.jsonl

# Solo session
grep '"cmd": "session\.' events.jsonl
```
