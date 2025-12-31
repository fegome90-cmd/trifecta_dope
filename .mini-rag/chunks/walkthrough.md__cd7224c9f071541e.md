## T6 — fullfiles fallback (non-default)
**Objetivo**: Proveer fallback robusto.

- **Archivos tocados**:
  - `src/application/use_cases.py` (`MacroLoadUseCase`)
- **Cambios concretos**:
  - Soporte explícito de `--mode fullfiles`.
- **Comandos ejecutables**:
  - `trifecta load --segment . --task "legacy" --mode fullfiles`
- **DoD / criterios de aceptación**:
  - Carga completa verificada.
- **Riesgos mitigados**:
  - **Inaccesibilidad**: Garantizada continuidad operativa.

---
