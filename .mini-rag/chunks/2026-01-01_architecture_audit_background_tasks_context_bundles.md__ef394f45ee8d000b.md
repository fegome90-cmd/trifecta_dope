**RIESGO CRÍTICO DETECTADO**:  
`context_pack.json` puede ser corrompido por `trifecta ctx build` concurrente (ej: 2 agentes corriendo `build` en paralelo). NO hay lock ni versioning.

---
