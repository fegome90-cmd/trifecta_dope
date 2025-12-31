### 5. Contra la Ilusión del Pensamiento: **Verificación de Coherencia (The Judge)**

*El problema:* El agente dice "Voy a usar encriptación" y luego escribe código en texto plano.

**Solución Técnica:** **Paso de Alineación Semántica.**
Antes de pasar al linter, usamos un modelo pequeño y rápido (ej. GPT-3.5-turbo o un modelo local cuantizado) como "Juez de Coherencia".

* **Prompt del Juez:**
> "Aquí está el PLAN del agente: [X]. Aquí está el CÓDIGO generado: [Y].
> ¿El código implementa *fielmente* el plan? Responde SI/NO. Si es NO, explica qué falta."


* **Efecto:** Si el agente alucina cumplimiento, el Juez lo atrapa antes de gastar recursos en ejecución. Esto conecta la "intención" con la "implementación".

---
