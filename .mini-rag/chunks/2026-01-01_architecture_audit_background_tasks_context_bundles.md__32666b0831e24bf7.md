### A.1 CLI → Bundle Recorder Hook

**Archivo**: `src/infrastructure/cli.py`

**Punto de inserción**: Inicio de cada comando (después de `_get_telemetry`, antes de UseCase.execute).

```python
# cli.py (ejemplo en ctx_app.command("search"))

@ctx_app.command("search")
def search(...):
    telemetry = _get_telemetry(segment, telemetry_level)

    # NUEVO: Bundle recorder hook
    bundle_recorder = None
    if typer.get_context().params.get("bundle_capture", False):
        bundle_recorder = BundleRecorder(segment, run_id=telemetry.run_id)
        bundle_recorder.start_session("ctx search", {"query": query, "limit": limit})

    use_case = SearchUseCase(file_system, telemetry, bundle_recorder)  # Inject recorder
    # ...
```

**Impacto**: Cada comando necesita pasar `bundle_recorder` a UseCase (signature change).

---
