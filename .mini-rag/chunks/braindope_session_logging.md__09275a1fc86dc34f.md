#### Pregunta #3: ¿Dos JSONL vs Event Type?
**Opciones**:
- A) Dos archivos separados (session_journal.jsonl + telemetry)
- B) Un archivo (telemetry con event type `session.entry`)

**Justifica tu elección con**:
- Query performance (¿importa?)
- Separación de concerns (¿por qué crítico?)
- Costo de mantenimiento (¿dos schemas forever?)

**ELIGE Y JUSTIFICA**
**Timestamp**: 11:05
**Vector Aplicado**: Internal Inconsistency

**Red Team ataca**:
```
CONTRADICCIÓN FLAGRANTE:

Statement A: North Star = "pocos tokens, poco tiempo"
Statement B: "session.md puede crecer cuanto necesite"

PRUEBA:
Si session.md crece indefinidamente → eventualmente será > 5000 tokens → viola "pocos tokens"

¿Cuál es verdad?
- ¿session.md es para humanos y NO se carga en prompt?
- ¿O session.md SÍ se carga y debe mantenerse pequeño?

ELIGE UNO. No puedes tener "puede crecer indefinidamente" + "pocos tokens" al mismo tiempo.
```

**Usuario responde**:
[ESPERANDO RESPUESTA - ¿session.md va en el prompt del agente o no?]

---
