#### File Watcher (Hook)

**Mantener frescos**:
```python
# Cada vez que agente edita
def on_file_change(file_path: Path):
    if file_path in hotset:
        # Recalcular incremental
        hotset_cache.update(file_path)
        # Actualizar índices
        symbol_index.rebuild(file_path)
```

---
