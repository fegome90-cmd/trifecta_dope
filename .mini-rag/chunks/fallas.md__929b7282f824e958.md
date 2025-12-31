### 1. Contra la Falacia Estática: **Property-Based Testing (Fuzzing)**

*El problema:* El agente escribe `def suma(a, b): return 4` y el test `assert suma(2, 2) == 4` pasa. El linter pasa. El código es basura.

**Solución Técnica:**
Abandonamos los Unit Tests simples. Exigimos **Property-Based Testing** (usando la librería `hypothesis` en Python).

* **La Regla:** El agente no debe probar casos específicos ("2+2=4"). Debe probar **invariantes**.
* **Implementación:**
El agente debe generar:
```python
@given(st.integers(), st.integers())
def test_suma_propiedad_conmutativa(x, y):
    assert suma(x, y) == suma(y, x)

```


* **Efecto:** El runner ejecuta este test con 100 inputs aleatorios (fuzzing). Si el código es frágil o "hackeado" para un solo caso, explotará.
