#### 3.2.3 Comandos CLI Nuevos

```bash
# Iniciar background task
trifecta background start "ctx build --segment ."
# Output: Task started: task_abc123

# Listar tasks activos
trifecta background ps
# Output:
# task_abc123  RUNNING  ctx build  2min ago
# task_def456  DONE     ctx sync   5min ago

# Ver output de task
trifecta background tail task_abc123
# Output: [streaming last 20 lines]

# Cancelar task
trifecta background cancel task_abc123
# Output: Task cancelled (SIGTERM sent)
```
