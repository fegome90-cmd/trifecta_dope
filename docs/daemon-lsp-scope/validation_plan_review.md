Review del Plan de Validación

**Fecha**: 2026-03-22
**Input**: `docs/daemon-lsp-scope/validation_plan.md`

---

## Summary

Plan de validación con 5 validaciones. Estructura correcta.

## Major Issues (1)

### M1: V5 sin verificación de pyright

**Problema**: No se verifica si pyright está instalado antes de V5.
**Recomendación**: Agregar `which pyright || echo "pyright not installed, skipping V5"`

## Minor Issues (2)

### m1: V3 sin timeout

**Problema**: No se define cuánto esperar para verificar singleton.
**Recomendación**: Agregar timeout de 5s.

### m2: V2 asume daemon corriendo

**Problema**: No se incluye paso de inicio antes de V2.
**Recomendación**: Agregar `trifecta daemon start --repo .` antes de V2.

## Veredicto

**Approved con ajustes menores**.
