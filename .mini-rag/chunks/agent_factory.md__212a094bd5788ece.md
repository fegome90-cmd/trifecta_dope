```

### 3. Integración en el Flujo de Trabajo

Ahora el comando `trifecta ctx build` hace dos cosas:

1. **Para el LLM (Contexto):** Lee el `AGENTS.md` y se lo inyecta como texto plano en el System Prompt.
* *Efecto:* El agente "sabe" las reglas y trata de seguirlas.


2. **Para la Máquina (Validación):** Ejecuta el compilador (`compiler.py`), genera `sgconfig.yml` temporal y corre el scan.
* *Efecto:* Si el agente "olvidó" una regla, la máquina lo atrapa.



### Reto Técnico: La regla `function-style` (Puros vs Impuros)

Esta es la más difícil de transpilar a un linter estático simple (`ast-grep`).

* **Tu definición:** "Las funciones deben ser puras".
* **El problema:** Detectar impureza estáticamente es difícil.
* **La solución aproximada (Heurística):**
En lugar de detectar "pureza", detectamos "impureza obvia".
*Traducción del compilador para `pure-function`:*
```yaml
- id: pure-services
  message: Función impura detectada en servicio. Evita I/O, random o estado global.
  severity: warning
  rule:
    any:
      - pattern: Math.random()
      - pattern: Date.now()
      - pattern: console.log($$$)
      - pattern: fs.readFile($$$)
      - pattern: fetch($$$)
  inside:
    subdir: src/services
