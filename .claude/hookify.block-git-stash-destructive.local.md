---
name: block-git-stash-destructive
enabled: true
event: bash
pattern: git\s+stash\s+(drop|clear|pop)
action: block
---

**PROTECCION DE GIT STASH ACTIVADA**

Estás intentando ejecutar un comando destructivo de git stash:
- `git stash drop` - Elimina un stash permanentemente
- `git stash clear` - Elimina TODOS los stashes
- `git stash pop` - Aplica y elimina (preferir `git stash apply`)

**REGla personal del usuario:**
> "BORRASTE MUCHOS DATOS!!!" - Incidente 2025-12-27
> Perdida del 95.56% de resultados de evaluación por stash drop accidental

**Acciones permitidas:**
- `git stash list` - Ver stashes
- `git stash apply` - Aplicar sin eliminar
- `git stash push -m "mensaje"` - Crear nuevo stash

Si realmente necesitas eliminar un stash, solicita confirmación explícita del usuario primero.
