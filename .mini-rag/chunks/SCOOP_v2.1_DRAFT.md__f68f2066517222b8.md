## 12) Policy de decisiones (prioridades ordenadas)

**TRADE-OFFS** (orden descendente):

1. **Correctness > Performance**
   Justificación: Reliable writes > fast writes. Si hay trade-off, priorizar data integrity.

2. **Backward compatibility > Elegancia**
   Justificación: Scripts/CI no pueden romperse. Schema legacy es aceptable si mantiene compat.

3. **Simplicidad > Features**
   Justificación: North Star "60 segundos". Cada feature añade complejidad que viola esto.

4. **Pragmatismo > Purismo arquitectónico**
   Justificación: Mixing session + telemetry es pragmático. Separación semántica es nice-to-have.

5. **Evidence > Assumptions**
   Justificación: Claims sin metrics son rechazados. Benchmark dataset obligatorio.

---
