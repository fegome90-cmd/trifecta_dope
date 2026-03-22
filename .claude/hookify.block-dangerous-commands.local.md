---
name: block-dangerous-commands
enabled: true
event: bash
pattern: (rm\s+-rf|dd\s+if=|mkfs|chmod\s+777|>\s*/dev/sd|curl\s+.*\|\s*bash|wget\s+.*\|\s*bash)
action: block
---

**COMANDO PELIGROSO DETECTADO**

Estás intentando ejecutar un comando potencialmente destructivo:

| Comando | Riesgo |
|---------|--------|
| `rm -rf` | Eliminación recursiva sin confirmación |
| `dd if=` | Sobrescribe dispositivos |
| `mkfs` | Formatea discos |
| `chmod 777` | Permisos inseguros |
| `> /dev/sd*` | Escribe directamente a discos |
| `curl \| bash` | Ejecuta código remoto sin verificación |

**Antes de ejecutar:**
1. Verifica la ruta COMPLETA
2. Confirma con el usuario
3. Considera alternativas más seguras

**Alternativas:**
- `rm -rf` → `rm -i` (interactivo) o `trash-cli`
- `chmod 777` → Permisos específicos (750, 640)

Solicita confirmación explícita: "¿Estás seguro de ejecutar [comando]? Esta acción no se puede deshacer."
