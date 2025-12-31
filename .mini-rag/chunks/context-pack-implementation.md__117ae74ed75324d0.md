### Ejemplo de Scoring

| Chunk Title | Level | Keywords | Score |
|-------------|-------|----------|-------|
| "Core Rules" | 2 | "core", "rules" | 3+2=5 |
| "Overview" | 2 | "overview" (<300 chars) | -2 |
| "Commands" | 2 | "commands" | 3+2=5 |
| "Deep Nested Section" | 4 | - | 0 |

**Resultado**: Digest selecciona "Core Rules" y "Commands" (score 5), omite "Overview" (score -2).

---
