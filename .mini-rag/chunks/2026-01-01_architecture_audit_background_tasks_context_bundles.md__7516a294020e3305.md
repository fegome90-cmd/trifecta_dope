**Hallazgo crítico**: El pipeline actual tiene **3 riesgos split-brain** (telemetry.py flock, context_pack.json sin lock, session.md append sin coordinator), **2 bloat vectors** (node_modules y .git pueden ser capturados por bundles si no hay denylist estricta), y **cero instrumentación para tool-call recording** (no hay hooks entre CLI → UseCase → FileSystem). **NUEVO**: PCC Metrics (feature_map evaluation) ya implementados proveen base para medir bundle effectiveness.

**Cambios Clave Integrados (PR #1 + 54 commits)**:
- **PCC Metrics**: `parse_feature_map()`, `evaluate_pcc()`, `summarize_pcc()` para medir path_correct, false_fallback, safe_fallback
- **Result Monad**: `Ok[T] | Err[E]` para Railway Oriented Programming (domain layer)
- **FP Gate**: `validate_segment_fp()` wrapper con fail-closed validation
- **Router v1**: Calibrado y frozen (guardrails hardened)
- **Whole-file Chunking (T2)**: IDs estables, chunking_method tracking
- **Context Pack v1 Schema (T1)**: Manifest con digest, index, chunks
