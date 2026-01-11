## 🔴 PROBLEMA #2: Propósito Conflictivo

**Telemetry está diseñado para**:
- Performance profiling (timing_ms)
- Error tracking (warnings, result.status)
- Debugging de infraestructura (¿por qué LSP falló?)

**Session está diseñado para**:
- Onboarding de agentes ("¿qué hizo el agente anterior?")
- Context recall ("¿en qué archivos trabajamos en debug?")
- Decision tracking ("¿por qué elegimos approach X?")

**Si mezclas ambos**:
- Telemetry se contamina con datos narrative que no son métricas
- Session pierde claridad al mezclarse con ruido de infraestructura

---
