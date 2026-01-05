### 3. Contra la Explosión de Estado: **Memory Compression Pipeline**

*El problema:* Pasar `[State_0, ..., State_50]` quiebra la ventana de contexto.

**Solución Técnica:** **Compresión Recursiva con Pérdida Semántica.**
Introducimos un paso de "Sueño REM" en el pipeline. Cada N pasos, el sistema comprime el historial.

```python
def compress_state(history: List[Event]) -> Summary:
    # Usa un modelo barato/rápido para resumir
    summary = llm.summarize(
        history,
        keep=["decisiones_arquitectonicas", "errores_encontrados"],
        discard=["codigo_fallido_intermedio", "logs_verbose"]
    )
    return summary

```

* **Efecto:** El agente siempre ve: `[Resumen_Compacto] + [Últimos_5_Pasos]`. Mantiene la "memoria a largo plazo" sin el costo de la "memoria fotográfica".
