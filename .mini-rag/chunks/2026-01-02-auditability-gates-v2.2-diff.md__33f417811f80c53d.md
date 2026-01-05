## Cómo aplicar v2.2

```bash
# 1. Aplicar patch A) en src/domain/context_models.py
# 2. Reemplazar fila G3 en tabla del plan con patch B)
# 3. Reemplazar sección G3 en audit_repro.sh con patch C)
# 4. Reemplazar test con patch D)

# Verificar:
rg "model_dump\(mode=\"json\"\)" src/domain/context_models.py  # Debe encontrar
rg "g3_status.txt" docs/plans/...audit_repro.sh  # Debe encontrar
rg "prime_test_segment.md" tests/...test_path_hygiene_e2e.py  # Debe encontrar
```
