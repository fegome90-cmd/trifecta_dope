#### 4. La Actualización Explícita (`ctx update`)

Para aceptar el cambio (por ejemplo, editaste la skill legítimamente), debes ejecutar un comando consciente:

```bash
trifecta ctx update --skill python-expert

```

Este comando:

1. Calcula el nuevo hash.
2. Te muestra un **diff** (Reporte) de qué cambió.
3. Actualiza el `trifecta.lock` con el nuevo hash.

---
