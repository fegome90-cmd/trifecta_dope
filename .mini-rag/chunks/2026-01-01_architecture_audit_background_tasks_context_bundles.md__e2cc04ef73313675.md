### 5.2 Riesgo R2: node_modules / .git Bloat

**Descripción**: Si `scan_files()` captura `node_modules/` o `.git/`, bundle puede ser GBs.

**Impacto**: ALTO (disk exhaustion, bundle unshippable).

**Probabilidad**: MEDIA (fácil de triggerear con workspace con node_modules).

**Mitigación**:
1. **Preventivo**: Hardcoded denylist en `FileSystemAdapter.scan_files()` (además de policy YAML).
2. **Detective**: Check `bundle_size_mb` antes de finalize, abort si > 10MB.
3. **Correctivo**: Comando `trifecta bundle prune <run_id>` para eliminar bloat post-mortem.
4. **Validación**: Test `test_bundle_scan_excludes_node_modules` con workspace real.

**Métrica**: `excluded_paths_count` debe ser > 0 en workspaces típicos.

---
