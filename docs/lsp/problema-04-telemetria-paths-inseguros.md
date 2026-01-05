# Problema 4: Telemetría con Paths Potencialmente Inseguros

**Prioridad**: 🟢 BAJA | **Estimado**: 3h | **Fecha**: 2026-01-05

---

## Problema

Telemetría usa `relative_to()` que falla con paths fuera del workspace (symlinks, temp files). Potencial leak de PII (usernames en paths).

**Ubicación**: [cli_ast.py:84](../../src/infrastructure/cli_ast.py#L84), [cli.py](../../src/infrastructure/cli.py) (~15 lugares)

---

## Solución

Crear helper `sanitize_path()` con try/except:
- ✅ Dentro workspace → path relativo
- ✅ Fuera workspace → solo nombre
- ✅ PII-safe

---

## Documentos Complementarios

- **Análisis detallado**: [problema-04-analisis.md](problema-04-analisis.md)
- **Implementación**: [problema-04-implementacion.md](problema-04-implementacion.md)
- **Tests**: [problema-04-tests.md](problema-04-tests.md)

---

## Timeline

- Crear helper: 30min
- Actualizar usos: 1.5h
- Tests + policy: 1h
- **Total: 3h**
