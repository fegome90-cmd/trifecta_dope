# Fase 0 - Baseline y Contrato: CLI Opciones Inválidas

**WO**: WO-0022  
**Fecha**: 2026-02-10  
**Estado**: Baseline definido

---

## 0.1 Contrato de Éxito

### KPI Primario: `invalid_option_count`

| Métrica | Definición | Objetivo |
|---------|------------|----------|
| invalid_option_count | Número de errores "No such option" por sesión de agente | **0** en sesiones normales |

**Rationale**: Un agente bien informado no debería intentar usar flags que no existen. Cada error representa:
- Fricción en el flujo de trabajo
- Tokens gastados en error + recovery
- Tiempo perdido en ciclo de prueba-error

### KPI Secundario: `help_first_used`

| Métrica | Definición | Objetivo |
|---------|------------|----------|
| help_first_used | Porcentaje de veces que el agente consulta `--help` antes de intentar flags desconocidos | **≥80%** cuando hay flags raros |

**Rationale**: El comportamiento deseado es:
1. Ante duda → `command --help`
2. Identificar flags válidos → usar correctamente
3. No intentar flags inventados

### Definition of Done (DoD) Global

> Cuando se comete un error de opción inválida, el CLI entrega **instrucción accionable** (help + ejemplos) y el agente **converge sin repetir**.

**Criterios**:
- [ ] Error message incluye sugerencia de `--help`
- [ ] Error message lista flags similares (si aplica)
- [ ] Ejemplo de uso correcto incluido
- [ ] El agente puede resolver sin iteraciones adicionales

---

## 0.2 Evidencia Actual

### Muestra 1: `--dry-run` en `trifecta load`

**Comando**:
```bash
uv run trifecta load --segment . --task "Implement error handling" --dry-run
```

**Error**:
```
Usage: trifecta load [OPTIONS]
Try 'trifecta load --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such option: --dry-run                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Análisis**:
- Flag asumida por patrón común en otros CLIs
- No existe en `trifecta load`
- Mensaje de error no sugiere alternativa
- El agente debe ejecutar `--help` para descubrir opciones válidas

**Log**: `_ctx/logs/WO-0022_dry_run_error.log`

---

### Muestra 2: `--max-steps` en `trifecta ctx plan`

**Comando**:
```bash
uv run trifecta ctx plan --segment . --task "Add new CLI command" --max-steps 5
```

**Error**:
```
Usage: trifecta ctx plan [OPTIONS]
Try 'trifecta ctx plan --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such option: --max-steps                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Análisis**:
- Flag asumida por patrón de planes con límite de pasos
- No existe en `trifecta ctx plan`
- Mismo problema: mensaje genérico sin ayuda contextual

**Log**: `_ctx/logs/WO-0022_max_steps_error.log`

---

## Métricas de Baseline

### Conteo de Errores por Tipo

| Tipo de Error | Frecuencia Observada | Severidad |
|---------------|---------------------|-----------|
| `--dry-run` no existe | 1/15 comandos | Media |
| `--max-steps` no existe | 1/15 comandos | Media |
| **Total invalid_option_count** | **2/15 (13.3%)** | - |

### Comportamiento del Agente

| Métrica | Valor Observado | Objetivo | Gap |
|---------|----------------|----------|-----|
| invalid_option_count | 2 | 0 | +2 |
| help_first_used | 0% | ≥80% | -80% |
| convergencia sin repetir | 0% | 100% | -100% |

---

## Contrato Propuesto

### Para CLI (Responsabilidad del Sistema)

Cuando ocurre `No such option`:

1. **Mostrar flags similares** (fuzzy match)
2. **Sugerir `--help`** explícitamente
3. **Incluir ejemplo** de uso correcto
4. **(Futuro)** Link a documentación

Ejemplo de salida deseada:
```
❌ Error: No such option: --dry-run

Posiblemente quisiste decir:
  --help          Show help message

Para ver opciones disponibles:
  uv run trifecta load --help

Ejemplo de uso:
  uv run trifecta load --segment . --task "Implement feature X"
```

### Para Agente (Responsabilidad del Usuario)

1. **Siempre verificar `--help`** antes de usar flags desconocidos
2. **No asumir flags** basados en otros CLIs
3. **Loggear el error** como evidencia de fricción

---

## Dataset para Tests / Regresión

```python
# tests/integration/test_cli_invalid_options.py (esqueleto)
INVALID_OPTIONS_DATASET = [
    {
        "command": ["trifecta", "load", "--segment", ".", "--task", "test", "--dry-run"],
        "invalid_flag": "--dry-run",
        "suggested_help": "trifecta load --help",
    },
    {
        "command": ["trifecta", "ctx", "plan", "--segment", ".", "--task", "test", "--max-steps", "5"],
        "invalid_flag": "--max-steps",
        "suggested_help": "trifecta ctx plan --help",
    },
]
```

---

## Próximos Pasos

1. **Fase 1**: Implementar mensajes de error mejorados con sugerencias
2. **Fase 2**: Agregar fuzzy matching para flags similares
3. **Fase 3**: Documentar contrato en skill.md / CLAUDE.md
4. **Fase 4**: Tests de regresión con dataset de baseline

---

## Referencias

- **WO**: `_ctx/jobs/pending/WO-0022.yaml`
- **Logs**: `_ctx/logs/WO-0022_*.log`
- **Error Cards**: `src/cli/error_cards.py`
- **CLI Workflow**: `docs/CLI_WORKFLOW.md`

---

*Baseline establecido. Listo para Fase 1: Implementación.*
