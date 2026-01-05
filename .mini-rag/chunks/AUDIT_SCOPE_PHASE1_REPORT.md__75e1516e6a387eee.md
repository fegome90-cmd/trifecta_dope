**Verificaciones de Invariantes en Telemetría:**
- ✅ `timing_ms >= 1`: Todos los eventos tienen `timing_ms` mínimo de 1
- ✅ `segment_id = 6f25e381` (8 chars): Consistente
- ✅ No PII: No hay rutas absolutas tipo `/Users/...` en los eventos
- ✅ `run_id` único por comando ejecutado
- ✅ `x` namespace presente para metadata extendida

---
