### Comportamiento de `trifecta load`
- **Por defecto (Macro Plan A)**: Ejecuta internamente `ctx search` + `ctx get` (modo PCC).
- **Fallback Forzado**: `--mode fullfiles` activa Plan B (archivos completos heurísticos).

- **Comandos ejecutables**:
  - **Core (Plan A)**:
    - `trifecta ctx search --segment . --query "locks" --limit 6`
    - `trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900`
  - **Fallback/Macro**:
    - `trifecta load --segment . --task "investigate legacy auth" --mode fullfiles`
- **DoD / criterios de aceptación**:
  - Existencia de sección NO-GO.
  - Definición clara de la política "1 search + 1 get" por turno.
  - Semántica de `load` definida: PCC por defecto, Fullfiles bajo demanda.
- **Riesgos mitigados**:
  - **Ambigüedad arquitectónica**: Eliminada al definir roles claros para Plan A y B.
  - **Deriva de alcance**: Mitigada con la sección NO-GO.

---
