## 🤔 LA PREGUNTA CORRECTA

**No es**: "¿Podemos usar telemetry?"  
**Es**: "¿DEBERÍAMOS usar telemetry?"

**Trade-off**:
- **Opción A**: Extender telemetry → Un solo JSONL, pero semánticamente sucio
- **Opción B**: Session JSONL separado → Dos archivos, pero semánticamente limpio

**Mi recomendación escéptica**:
Si el overlap fuera 95%, diría "usa telemetry".  
Pero el overlap es de granularidad (task vs comando), no de datos.  
Son **propósitos diferentes** con **niveles de abstracción diferentes**.

**Necesito que respondas**:
1. ¿Session entries van en el prompt del agente (alto valor) o solo son para query (bajo valor)?
2. ¿Tolerarías que session search traiga ruido de lsp.spawn, ctx.sync?
3. ¿El costo de DOS archivos JSONL realmente te duele, o es acceptable?

**NO implementes hasta responder estas 3.**
