### 2. Contra la Paradoja Rígida: **Constitución JIT (Just-in-Time)**

*El problema:* `AGENTS.md` monolítico confunde al modelo o lo hace rígido.

**Solución Técnica:** **Retrieval-Augmented Governance.**
No inyectes todo el `AGENTS.md`. Divide tu constitución en "Principios" (Universales) y "Reglas" (Contextuales).

* **Implementación:**
1. Fragmenta `AGENTS.md` en vectores.
2. Cuando el agente recibe la tarea "Crear endpoint API", el sistema hace una búsqueda semántica.
3. **Inyección Dinámica:** Solo se inyectan las reglas de "Seguridad API" y "Controladores". Las reglas de "Base de Datos" se omiten para reducir ruido y rigidez.


* **Efecto:** El agente recibe una constitución fresca y específica para la misión, reduciendo el overfitting a reglas irrelevantes.
