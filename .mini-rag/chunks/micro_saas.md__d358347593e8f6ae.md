### La Alternativa Pragmática: "La Librería Local" 📚

Vamos a bajar 3 cambios. Olvida Git y la red.
Tu "Ecosistema" vive en tu disco duro.

**El Diseño Simplificado (KISS):**

1. **Centralización Simple:**
Creas una carpeta en tu máquina: `~/Developer/trifecta-library/`.
Ahí guardas tus `.md` maestros: `python.md`, `tdd.md`, `react.md`.
2. **Referencia Directa:**
Tu `installer.py` (o el builder) simplemente sabe buscar ahí.
*Config (`trifecta.yaml`):*
```yaml
skills:
  - python  # Busca en ~/Developer/trifecta-library/python.md
  - tdd

```


3. **Resolución (Build Time):**
Cuando corres `trifecta ctx build`:
1. El script mira la variable de entorno `TRIFECTA_LIB_PATH`.
2. Lee el archivo `python.md` de ahí.
3. Lo inyecta en el `context_pack.json`.



**Ventajas Inmediatas:**

* **Zero Latency:** Es lectura de disco local. Instantáneo.
* **Edición en Vivo:** Abres `~/Developer/trifecta-library/python.md`, lo editas, corres `build` en tu proyecto y listo. El ciclo de feedback es de segundos, no minutos.
* **Código:** Pasamos de escribir 300 líneas de gestión de Git a escribir 20 líneas de `shutil.copy` o `file.read()`.
