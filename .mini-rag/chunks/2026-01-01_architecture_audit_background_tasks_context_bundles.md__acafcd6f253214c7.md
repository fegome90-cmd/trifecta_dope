#### 3.1.4 Rollback Plan

- Si `BundleRecorder` causa crashes: Deshabilitar con `--bundle-capture=false` (default).
- Si policy YAML es inválido: Fallar ruidosamente (`ctx bundle show` muestra error, no silent fallback).
- Si manifest corrupto: Eliminar `_ctx/bundles/<run_id>/` y re-run sin bundle capture.

---
