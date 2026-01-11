### E.2) BLOCKING GAPS (ordenados por criticidad)

| # | Blocker | Tipo | Impacto | Dificultad | Tiempo Est. |
|---|---------|------|---------|------------|-------------|
| **1** | session append dual write (telemetry + .md) | Code | CRÍTICO - rompe tests | Baja | 2h |
| **2** | JSON schemas en archivos separados | Infrastructure | Alto - sin validadores | Media | 3h |
| **3** | scripts/bench_session_query.py (determinista) | Scripts | Alto - métricas inválidas | Media | 4h |
| **4** | Definir tokens vs bytes para efficiency | Spec | Medio - threshold unclear | Baja | 1h |
| **5** | scripts/generate_benchmark_dataset.py | Scripts | Medio - dataset inexistente | Media | 3h |
| **6** | Verificar _sanitize_event cubre session.entry | Audit | Medio - privacy risk | Baja | 1h |
| **7** | tests/acceptance/test_no_privacy_leaks.py | Tests | Medio - sin gate automático | Baja | 2h |

**TOTAL ESTIMADO**: 16 horas (matches SCOOP estimate)

---
