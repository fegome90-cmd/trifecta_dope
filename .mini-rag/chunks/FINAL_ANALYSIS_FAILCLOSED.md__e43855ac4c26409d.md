### DECISIÓN FINAL BASADA EN EVIDENCIA

**ELIJO**: **Opción A (Dual Write)**

**Razones**:
1. ✅ AUDIT:L95 recomienda explícitamente dual write
2. ✅ braindope:L468 usuario decidió "mantener session.md"
3. ✅ FINAL_PROPOSAL:L135-L140 menciona "append a telemetry + sync md"
4. ✅ Cero tests rotos
5. ✅ Camino más seguro (fail-closed)

**Evidencia que confirma dual write es la decisión**:
> FINAL_PROPOSAL:L134-L136:  
> # Hace DOS cosas:  
> # 1. Append a telemetry.jsonl (source of truth)  
> # 2. Regenera session.md DESDE telemetry (opcional, si --sync-md flag)

**INTERPRETACIÓN CORRECTA**:
- V1: Dual write (ambos)
- V2: Opcional `--sync-md` flag para regenerar completo desde JSONL

---
